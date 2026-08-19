"""AI 生图服务（通义万相 / DashScope）

- 配置读取：SystemConfig 表优先，环境变量(.env)作为回退
- 文生图：默认 wan2.2-t2i-flash（可在管理员配置中修改）
- 图生图（带参考图）：wan2.5-i2i-preview
- 参考图支持 OSS 公网 URL，本地存储的 /static 路径会自动转为 base64 data URI
- 生成结果 URL 为 DashScope 临时地址，下载后转存到 OSS/本地，返回持久地址
"""
import base64
import io
import math
import mimetypes
import os
import urllib.request
from http import HTTPStatus
from typing import Optional

from fastapi import HTTPException

from app.config import settings
from app.database import SessionLocal
from app.models.system_config import SystemConfig
from app.services import upload_image_bytes

# 图生图专用模型（2026 年百炼有效模型；wanx2.1-i2i-turbo 已下架）
I2I_MODEL = "wan2.5-i2i-preview"
DEFAULT_T2I_MODEL = "wan2.2-t2i-flash"

# 万相 2.x 系列模型单边尺寸约束
MIN_EDGE = 512
MAX_EDGE = 1440

# 图生图（wan2.5-i2i-preview）输入图尺寸约束
I2I_MIN_EDGE = 384
I2I_MAX_EDGE = 5000
# 图生图输出总像素约束（错误提示: between 589824 (768*768) and 1638400 (1280*1280)）
I2I_MIN_PIXELS = 589824

# AI 生图用途：绑定微站系统真实图片使用场景，尺寸与约束词均为该用途定制
AI_USES: dict[str, dict[str, str]] = {
    "icon": {
        "label": "模块图标",
        "size": "128*128",
        "desc": "128×128 正方形，用于九宫格/按钮模块图标",
        "prompt_suffix": "，扁平化设计，纯色或渐变简洁背景，主体居中，无文字，无LOGO",
    },
    "kv": {
        "label": "KV 横幅",
        "size": "750*340",
        "desc": "750×340 宽幅横幅，用于微站顶部 KV 图",
        "prompt_suffix": "，宽幅横幅构图，左右留白，视觉重心居中，简洁大气，无文字，无LOGO",
    },
    "share": {
        "label": "微信分享图",
        "size": "500*500",
        "desc": "500×500 正方形，用于微信分享卡片",
        "prompt_suffix": "，正方形构图，主题突出，简洁清晰，无文字，无LOGO",
    },
    "background": {
        "label": "页面背景",
        "size": "750*1334",
        "desc": "750×1334 竖版，用于微站页面全屏背景",
        "prompt_suffix": "，竖版构图，大面积留白，低饱和渐变色调，适合作为页面全屏背景，无文字，无LOGO",
    },
}


def get_ai_config() -> dict[str, str]:
    """获取 AI 配置：数据库系统配置优先，环境变量作为回退。"""
    db = SessionLocal()
    try:
        config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
        return {
            "provider": (config.ai_provider if config and config.ai_provider else settings.AI_PROVIDER),
            "api_key": (config.ai_api_key if config and config.ai_api_key else settings.DASHSCOPE_API_KEY),
            "image_model": (config.ai_image_model if config and config.ai_image_model else settings.AI_IMAGE_MODEL),
        }
    finally:
        db.close()


def ai_is_configured() -> bool:
    """是否已配置 AI API Key"""
    return bool(get_ai_config()["api_key"])


def _ensure_reference_size(content: bytes) -> tuple[bytes, bool]:
    """校验参考图尺寸是否满足模型输入约束 [384, 5000]；不满足则按比例缩放（保持宽高比）。

    Returns:
        (处理后的图片字节, 是否发生了缩放)
    """
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(content))
        w, h = img.size
        min_edge, max_edge = min(w, h), max(w, h)
        if min_edge >= I2I_MIN_EDGE and max_edge <= I2I_MAX_EDGE:
            return content, False

        # 短边低于下限则放大，长边超过上限则缩小（两者叠加取最终比例）
        scale = 1.0
        if min_edge < I2I_MIN_EDGE:
            scale = max(scale, I2I_MIN_EDGE / min_edge)
        if max_edge * scale > I2I_MAX_EDGE:
            scale = I2I_MAX_EDGE / max_edge
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))

        # 极端宽高比（> 5000/384 ≈ 13:1）下无论如何缩放都无法同时满足上下限，直接提示换图
        if min(new_w, new_h) < I2I_MIN_EDGE or max(new_w, new_h) > I2I_MAX_EDGE:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"参考图尺寸 {w}x{h} 宽高比过大，无法适配模型输入范围"
                    f"[{I2I_MIN_EDGE}, {I2I_MAX_EDGE}]，请换用更接近 1:1 的参考图"
                ),
            )

        img = img.resize((new_w, new_h), Image.LANCZOS)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGBA")
        out = io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue(), True
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"参考图处理失败: {e}")


def _resolve_reference_image(reference_image_url: str) -> str:
    """参考图处理：获取图片字节 → 校验/缩放输入尺寸（保持宽高比）→ 转 base64 data URI。

    wan2.5-i2i-preview 要求输入图单边在 [384, 5000]，用户上传的小图标（如 100x100）
    低于下限会导致任务直接 FAILED，此处统一预检并按比例放大到合规尺寸。
    """
    if reference_image_url.startswith("/static/uploads/"):
        rel = reference_image_url[len("/static/uploads/"):]
        # 本文件在 app/services/ 下，dirname 三次回到 backend 根目录
        upload_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            settings.UPLOAD_DIR,
        )
        path = os.path.join(upload_dir, rel)
        if not os.path.exists(path):
            raise HTTPException(status_code=400, detail="参考图文件不存在")

        mime_type, _ = mimetypes.guess_type(path)
        with open(path, "rb") as f:
            content = f.read()
    else:
        # OSS 公网 URL：下载字节，保证能统一预检输入尺寸
        content = _download_bytes(reference_image_url, desc="参考图")
        mime_type, _ = mimetypes.guess_type(reference_image_url.split("?")[0])

    content, resized = _ensure_reference_size(content)
    if resized:
        mime_type = "image/png"  # 缩放后统一为 PNG
    if not mime_type or not mime_type.startswith("image/"):
        mime_type = "image/png"
    encoded = base64.b64encode(content).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def _download_bytes(url: str, desc: str = "生成结果") -> bytes:
    """下载图片内容（DashScope 返回的临时 URL / OSS 公网参考图）"""
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            return resp.read()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"下载{desc}失败: {e}")


def _output_results(output) -> list:
    """从 DashScope output 中安全提取 results 列表（兼容对象与 dict）"""
    if output is None:
        return []
    if isinstance(output, dict):
        return output.get("results") or []
    return getattr(output, "results", None) or []


def _result_url(item) -> Optional[str]:
    """从 results 元素中安全提取 url（兼容对象与 dict）"""
    if isinstance(item, dict):
        return item.get("url")
    return getattr(item, "url", None)


def _resize_image_bytes(content: bytes, width: int, height: int) -> bytes:
    """把图片字节精确缩放为指定宽高（返回 PNG 字节）。"""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(content))
        img = img.resize((width, height), Image.LANCZOS)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGBA")
        out = io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"生成结果缩放失败: {e}")


def _plan_size(size: str, min_pixels: int = 0) -> tuple[str, int, int]:
    """解析目标尺寸；若单边小于模型下限则按比例放大请求尺寸。

    Args:
        size: 目标尺寸，如 750*300
        min_pixels: 模型总像素下限（图生图 wan2.5-i2i-preview 需 ≥ 589824），
            单边放大后总像素仍不足时继续按比例放大

    Returns:
        (请求尺寸字符串, 目标宽, 目标高)
    """
    try:
        w, h = size.split("*")
        w, h = int(w), int(h)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"不支持的尺寸: {size}，格式应为 750*300")

    if w <= 0 or h <= 0 or w > MAX_EDGE or h > MAX_EDGE:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的尺寸: {size}，单边须在 1~{MAX_EDGE} 之间",
        )

    req_w, req_h = w, h
    min_edge = min(w, h)
    if min_edge < MIN_EDGE:
        # 放大请求尺寸，使短边达到模型下限，生成后再缩回目标尺寸
        scale = MIN_EDGE / min_edge
        req_w = min(MAX_EDGE, int(math.ceil(w * scale)))
        req_h = min(MAX_EDGE, int(math.ceil(h * scale)))
        if req_w > MAX_EDGE or req_h > MAX_EDGE:
            raise HTTPException(status_code=400, detail=f"不支持的尺寸: {size}，宽高比例过宽")
    if min_pixels > 0 and req_w * req_h < min_pixels:
        # 图生图模型对总像素有下限，继续放大直至满足
        pixel_scale = math.sqrt(min_pixels / (req_w * req_h))
        req_w = min(MAX_EDGE, int(math.ceil(req_w * pixel_scale)))
        req_h = min(MAX_EDGE, int(math.ceil(req_h * pixel_scale)))
        if req_w > MAX_EDGE or req_h > MAX_EDGE:
            raise HTTPException(status_code=400, detail=f"不支持的尺寸: {size}，宽高比例过宽")

    request_size = size
    if req_w != w or req_h != h:
        request_size = f"{req_w}*{req_h}"
    return request_size, w, h


def generate_images(
    prompt: str,
    negative_prompt: str = "",
    size: str = "1024*1024",
    n: int = 1,
    reference_image_url: Optional[str] = None,
    use: Optional[str] = None,
) -> tuple[list[str], str]:
    """调用通义万相生成图片。

    Args:
        prompt: 提示词
        negative_prompt: 负面提示词
        size: 生成尺寸，如 1024*1024；提供 use 时以用途预设尺寸为准
        n: 生成数量(1-4)，图生图固定为 1
        reference_image_url: 参考图 URL（可选），传入则走图生图
        use: 微站用途（icon/kv/share/background），提供时按用途预设尺寸，
            并在 prompt 尾部附加场景化约束词

    Returns:
        (持久化后的结果 URL 列表, 使用的模型名)
    """
    cfg = get_ai_config()
    if not cfg["api_key"]:
        raise HTTPException(status_code=400, detail="AI 生图未配置 API Key，请先在「管理员配置」中填写")

    # 按用途解析目标尺寸并附加场景化约束词（提高出图可用率）
    if use:
        if use not in AI_USES:
            raise HTTPException(status_code=400, detail=f"不支持的用途: {use}")
        use_info = AI_USES[use]
        size = use_info["size"]
        prompt = f"{prompt.strip()}{use_info['prompt_suffix']}"

    # 解析目标尺寸；低于模型下限的按比例放大请求，生成后再缩回目标尺寸
    is_i2i = bool(reference_image_url)
    if is_i2i:
        n = 1  # 图生图一次一张，保持接口简单可靠
        model = I2I_MODEL
        image_ref = _resolve_reference_image(reference_image_url)
        min_pixels = I2I_MIN_PIXELS
    else:
        n = max(1, min(int(n), 4))
        model = cfg["image_model"] or DEFAULT_T2I_MODEL
        image_ref = None
        min_pixels = 0
    request_size, target_w, target_h = _plan_size(size, min_pixels)

    try:
        from dashscope import ImageSynthesis

        kwargs = dict(
            model=model,
            prompt=prompt,
            size=request_size,
            n=n,
            api_key=cfg["api_key"],
        )
        if negative_prompt:
            kwargs["negative_prompt"] = negative_prompt
        # 2026 年新版万相模型（wan2.x 系列）图生图使用 images 参数；
        # 旧模型的 base_image_url 已随 wanx2.1-i2i 系列下架
        if image_ref:
            kwargs["images"] = [image_ref]

        rsp = ImageSynthesis.call(**kwargs)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"调用通义万相失败: {e}")

    if rsp.status_code != HTTPStatus.OK:
        message = getattr(rsp, "message", "") or str(rsp)
        code = getattr(rsp, "code", "") or ""
        # Model not exist：账号未开通该模型或模型已下架，给出可操作的修复指引
        if code == "InvalidParameter" and "Model not exist" in message:
            hint = (
                f"模型「{model}」不可用：请确认该模型已在阿里云百炼控制台开通"
                "（模型广场搜索该模型并开通），或在「管理员配置 → AI 生图 → 生图模型」中切换为其他模型"
                "（如 wan2.2-t2i-flash）。另请注意 API Key 的地域须与模型地域一致，不可跨地域混用。"
            )
            raise HTTPException(status_code=502, detail=f"AI 生图失败[{code}]: {message}。{hint}")
        raise HTTPException(status_code=502, detail=f"AI 生图失败[{code}]: {message}")

    output = rsp.output
    results = _output_results(output)

    # 任务非成功状态时透出真实原因，避免误报「未返回图片结果」
    task_status = getattr(output, "task_status", None)
    if isinstance(output, dict):
        task_status = output.get("task_status", task_status)
    if task_status and task_status != "SUCCEEDED":
        fail_msg = getattr(output, "message", "") or getattr(rsp, "message", "") or "无详细信息"
        if isinstance(output, dict):
            fail_msg = output.get("message") or getattr(rsp, "message", "") or "无详细信息"
        raise HTTPException(status_code=502, detail=f"AI 生成任务失败（{task_status}）: {fail_msg}")

    if not results:
        raise HTTPException(status_code=502, detail="AI 生成未返回图片结果")

    # 下载临时 URL 并转存到 OSS/本地（必要时缩回目标尺寸）
    need_downscale = request_size != f"{target_w}*{target_h}"
    persisted_urls: list[str] = []
    for item in results:
        temp_url = _result_url(item)
        if not temp_url:
            continue
        content = _download_bytes(temp_url)
        if need_downscale:
            content = _resize_image_bytes(content, target_w, target_h)
        persisted_urls.append(upload_image_bytes(content, ext="png"))

    if not persisted_urls:
        raise HTTPException(status_code=502, detail="AI 生成结果转存失败")

    return persisted_urls, model
