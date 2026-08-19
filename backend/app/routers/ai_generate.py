"""AI 生图路由：文生图/图生图、生成历史"""
import asyncio
import os
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import AIGeneration, User
from app.schemas.ai_generation import AIGenerationOut, PaginatedGenerations
from app.services import upload_image_bytes
from app.services import ai_generate as ai_service
from app.services import billing_service
from app.utils.deps import get_current_admin

router = APIRouter(prefix="/ai", tags=["AI生图"])


def _validate_reference(ext: str, content: bytes) -> str:
    """校验并保存参考图，返回持久化 URL（在 to_thread 中执行）"""
    if not ext or ext not in settings.allowed_file_types_list:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: .{ext or '未知'}，仅支持 {settings.ALLOWED_FILE_TYPES}")
    if not content:
        raise HTTPException(status_code=400, detail="参考图内容为空")
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"参考图大小超过限制({settings.MAX_FILE_SIZE // 1024 // 1024}MB)")
    return upload_image_bytes(content, ext=ext)


def _insufficient_detail(e: billing_service.InsufficientBalanceError) -> str:
    """余额不足的 403 提示文案"""
    unit = billing_service.AI_IMAGE_PRICE_CENTS / 100
    return (
        f"INSUFFICIENT_BALANCE:AI 生图按张扣费 {unit:.2f} 元，"
        f"当前余额 {e.balance / 100:.2f} 元，本次需要 {e.required / 100:.2f} 元，请联系管理员充值"
    )


@router.get("/config")
def read_ai_config(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """AI 生图配置状态（不含密钥明文），含价格与当前余额，供前端展示。"""
    cfg = ai_service.get_ai_config()
    owner = billing_service.get_billing_owner(db, current)
    return {
        "configured": bool(cfg["api_key"]),
        "provider": cfg["provider"],
        "image_model": cfg["image_model"],
        "i2i_model": ai_service.I2I_MODEL,
        "price_per_image_cents": billing_service.AI_IMAGE_PRICE_CENTS,
        "price_per_image_yuan": f"{billing_service.AI_IMAGE_PRICE_CENTS / 100:.2f}",
        "balance": owner.wallet_balance,
        "balance_yuan": f"{owner.wallet_balance / 100:.2f}",
        "is_free": current.role == "super_admin",  # 超级管理员 AI 生图免扣费
    }


@router.post("/generate", response_model=PaginatedGenerations)
async def generate_images(
    prompt: str = Form(..., min_length=1, max_length=2000),
    negative_prompt: str = Form("", max_length=2000),
    size: str = Form("750*300"),
    n: int = Form(1, ge=1, le=4),
    reference_image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """AI 生图：输入提示词（可选参考图走图生图），生成并保存到 OSS/本地，按张扣费并记录历史。"""
    if not ai_service.ai_is_configured():
        raise HTTPException(status_code=400, detail="AI 生图未配置 API Key，请先在「管理员配置」中填写")

    # 预检余额（按最多 n 张估算，实际按生成张数扣费）
    try:
        billing_service.assert_ai_generate_balance(db, current, n)
    except billing_service.InsufficientBalanceError as e:
        raise HTTPException(status_code=403, detail=_insufficient_detail(e))

    ref_url = None
    if reference_image:
        ext = os.path.splitext(reference_image.filename or "")[1].lower().lstrip(".")
        content = await reference_image.read()
        ref_url = await asyncio.to_thread(_validate_reference, ext, content)

    urls, model = await asyncio.to_thread(
        ai_service.generate_images, prompt, negative_prompt, size, n, ref_url
    )

    # 生成成功：按实际张数扣费并记录历史（同一事务提交）
    try:
        billing_service.charge_ai_generate(db, current, len(urls), remark=f"AI生图{len(urls)}张")
    except billing_service.InsufficientBalanceError as e:
        raise HTTPException(status_code=403, detail=_insufficient_detail(e))

    records: list[AIGeneration] = []
    for url in urls:
        rec = AIGeneration(
            user_id=current.id,
            prompt=prompt,
            negative_prompt=negative_prompt or None,
            reference_image=ref_url,
            result_url=url,
            provider="dashscope",
            model_name=model,
            size=size,
        )
        db.add(rec)
        records.append(rec)
    db.commit()
    for rec in records:
        db.refresh(rec)

    return {
        "total": len(records),
        "page": 1,
        "page_size": len(records),
        "items": [AIGenerationOut.model_validate(r) for r in records],
    }


@router.get("/generations", response_model=PaginatedGenerations)
def list_generations(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """分页查询当前用户的 AI 生成历史（按时间倒序）"""
    query = db.query(AIGeneration).filter(AIGeneration.user_id == current.id)
    total = query.count()
    items = (
        query.order_by(AIGeneration.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.delete("/generations/{generation_id}")
def delete_generation(
    generation_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """删除一条生成历史记录"""
    rec = (
        db.query(AIGeneration)
        .filter(AIGeneration.id == generation_id, AIGeneration.user_id == current.id)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="生成记录不存在")
    db.delete(rec)
    db.commit()
    return {"ok": True}
