#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用项目 DashScope 配置生成 6 个案例微站的实景感 KV 主视觉（750×340）

- API Key / 模型取自数据库 system_configs（ai_api_key / ai_image_model），无需改 .env
- 串行 + sleep 规避账号 QPS 限流（Throttling.RateQuota），失败自动重试
- 请求尺寸 1130×512（模型单边须 ≥512），生成后按比例裁切缩放到 750×340
- 覆盖前会把旧图备份到 seed_assets/demo/_pil_backup/（仅首次）

用法:
    cd backend && .venv/bin/python tools/gen_demo_kv_ai.py            # 生成全部
    .venv/bin/python tools/gen_demo_kv_ai.py --only kv_wedding       # 只生成一张
    .venv/bin/python tools/gen_demo_kv_ai.py --dry-run               # 只打印提示词
"""
import argparse
import io
import os
import shutil
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

OUT_DIR = os.path.join(BASE, "seed_assets", "demo")
BACKUP_DIR = os.path.join(OUT_DIR, "_pil_backup")
REQ_W, REQ_H = 1130, 512          # 请求尺寸（比例 2.207，与 750×340 一致）
OUT_W, OUT_H = 750, 340
SLEEP_BETWEEN = 4.0               # 每张之间停 4s，规避 QPS 限流
MAX_RETRY = 3

# 统一的收尾约束：横幅、留白、无文字水印
TAIL = ("横幅构图，主体居中偏右，画面上下留有干净空白，浅景深，摄影级写实质感，"
        "高级感，柔和自然光；画面中不要出现任何文字、字母、数字、LOGO、水印、招牌")

CASES = [
    ("kv_wedding", "户外婚礼现场，白色鲜花拱门与纱幔，两侧布置白色玫瑰与绿植，"
                   "阳光透过树叶洒下斑驳光影，白色座椅整齐排列，浪漫清新，米白与香槟金色调"),
    ("kv_course", "明亮的少儿编程教室，木质桌椅上有笔记本电脑，彩色积木与机器人教具，"
                  "蓝天窗外光，活泼的蓝橙配色，整洁现代的教育空间"),
    ("kv_summit", "大型行业峰会主会场，深蓝色舞台灯光与巨幅LED背景墙，"
                  "台下成排座椅与观众剪影，专业会议氛围，科技感深蓝紫色调"),
    ("kv_annual", "企业年会晚宴现场，红色与金色主题装饰，舞台暖光与金色灯球，"
                  "圆桌上铺着红桌布与金色烛台，喜庆热烈，红金配色"),
    ("kv_store", "温馨精品咖啡馆内景，木质吧台与手冲器具，白色陶瓷咖啡杯拉花特写在前景，"
                 "暖黄吊灯与绿植，午后阳光斜射，暖棕色调"),
    ("kv_chamber", "现代商务会议厅，深木色长条会议桌与皮质座椅，"
                   "窗外城市天际线与蓝天，庄重专业，商务蓝与浅灰配色"),
]


def get_ai_config() -> tuple[str, str]:
    """从数据库读取 DashScope API Key 与文生图模型"""
    from app.database import SessionLocal
    from app.models.system_config import SystemConfig

    db = SessionLocal()
    try:
        cfg = db.query(SystemConfig).first()
        key = (cfg.ai_api_key if cfg else "") or ""
        model = (cfg.ai_image_model if cfg else "") or "wan2.2-t2i-flash"
    finally:
        db.close()
    if not key:
        sys.exit("数据库中未配置 ai_api_key，请先在后台「管理员配置」里填写 DashScope API Key")
    return key, model


def backup_once(name: str):
    src = os.path.join(OUT_DIR, f"{name}.png")
    if not os.path.exists(src):
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    dst = os.path.join(BACKUP_DIR, f"{name}.png")
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
        print(f"  [备份] {name}.png -> _pil_backup/")


def gen_one(api_key: str, model: str, name: str, prompt: str) -> bool:
    from dashscope import ImageSynthesis
    from PIL import Image, ImageOps

    full_prompt = f"{prompt}，{TAIL}"
    for attempt in range(1, MAX_RETRY + 1):
        try:
            rsp = ImageSynthesis.call(
                api_key=api_key,
                model=model,
                prompt=full_prompt,
                n=1,
                size=f"{REQ_W}*{REQ_H}",
            )
            if rsp.status_code != 200:
                raise RuntimeError(f"{rsp.status_code} {getattr(rsp, 'message', '')}")
            results = (rsp.output or {}).get("results") or []
            url = results[0].get("url") if results else None
            if not url:
                raise RuntimeError(f"未返回图片 URL: {rsp.output}")

            import urllib.request
            with urllib.request.urlopen(url, timeout=60) as resp:
                raw = resp.read()

            img = Image.open(io.BytesIO(raw)).convert("RGB")
            img = ImageOps.fit(img, (OUT_W, OUT_H), Image.LANCZOS, centering=(0.5, 0.45))
            backup_once(name)
            out = os.path.join(OUT_DIR, f"{name}.png")
            img.save(out, "PNG", optimize=True)
            print(f"  [生成] {name}.png  {img.size[0]}×{img.size[1]}  "
                  f"{os.path.getsize(out) // 1024}KB  (第 {attempt} 次)")
            return True
        except Exception as e:  # noqa: BLE001
            print(f"  [重试 {attempt}/{MAX_RETRY}] {name}: {e}", file=sys.stderr)
            if attempt < MAX_RETRY:
                time.sleep(3 * attempt)
    print(f"  [失败] {name} 已达最大重试次数", file=sys.stderr)
    return False


def main():
    p = argparse.ArgumentParser(description="案例 KV 实景图生成")
    p.add_argument("--only", help="只生成指定的一张（不含 .png），如 kv_wedding")
    p.add_argument("--dry-run", action="store_true", help="只打印提示词，不调用接口")
    args = p.parse_args()

    targets = [c for c in CASES if not args.only or c[0] == args.only]
    if not targets:
        sys.exit(f"--only 未匹配到案例，可选：{', '.join(c[0] for c in CASES)}")

    if args.dry_run:
        for name, prompt in targets:
            print(f"\n[{name}]\n{prompt}，{TAIL}")
        print(f"\n共 {len(targets)} 张，尺寸 {REQ_W}×{REQ_H} -> {OUT_W}×{OUT_H}")
        return

    api_key, model = get_ai_config()
    print(f"模型: {model} | Key: {api_key[:6]}***{api_key[-4:]} | 共 {len(targets)} 张，串行执行\n")

    ok = []
    for i, (name, prompt) in enumerate(targets):
        if i:
            time.sleep(SLEEP_BETWEEN)
        ok.append(gen_one(api_key, model, name, prompt))

    print(f"\n完成 {sum(ok)}/{len(targets)} 张 -> {OUT_DIR}")
    if not all(ok):
        sys.exit(1)


if __name__ == "__main__":
    main()
