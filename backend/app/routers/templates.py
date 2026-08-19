"""微站模板管理路由"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, SiteTemplate
from app.utils.deps import get_current_admin, ROLE_SUPER_ADMIN, ROLE_ADMIN
from app.schemas.template import (
    SiteTemplateCreate, SiteTemplateUpdate, SiteTemplateOut,
    PaginatedSiteTemplates,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["微站模板"])


def _parse_modules_config(tpl: SiteTemplate) -> list[dict] | None:
    """将数据库中的 modules_config JSON 文本安全转换为列表。"""
    if not tpl.modules_config:
        return None
    try:
        return json.loads(tpl.modules_config)
    except (TypeError, json.JSONDecodeError):
        return None


def _parse_title_config(tpl: SiteTemplate) -> dict | None:
    """将数据库中的标题装饰配置 JSON 文本安全转换为字典。"""
    if not tpl.title_config:
        return None
    try:
        return json.loads(tpl.title_config)
    except (TypeError, json.JSONDecodeError):
        return None


def _to_out(tpl: SiteTemplate) -> SiteTemplateOut:
    return SiteTemplateOut(
        id=tpl.id,
        name=tpl.name,
        description=tpl.description,
        template_key=tpl.template_key,
        layout=tpl.layout,
        kv_image=tpl.kv_image,
        title_config=_parse_title_config(tpl),
        background_color=tpl.background_color,
        background_image=tpl.background_image,
        share_image=tpl.share_image,
        share_title=tpl.share_title,
        share_subtitle=tpl.share_subtitle,
        preview_image=tpl.preview_image,
        modules_config=_parse_modules_config(tpl),
        is_system=tpl.is_system,
        status=tpl.status,
        sort_order=tpl.sort_order,
        created_by=tpl.created_by,
        created_at=tpl.created_at,
        updated_at=tpl.updated_at,
    )


def _can_manage_templates(current: User) -> bool:
    """仅超管和管理员可增删改模板"""
    return current.role in (ROLE_SUPER_ADMIN, ROLE_ADMIN)


@router.get("", response_model=PaginatedSiteTemplates)
def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """模板列表(分页)"""
    q = db.query(SiteTemplate)
    if status:
        q = q.filter(SiteTemplate.status == status)
    if keyword:
        q = q.filter(SiteTemplate.name.like(f"%{keyword}%"))
    total = q.count()
    templates = q.order_by(SiteTemplate.sort_order.asc(), SiteTemplate.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [_to_out(t) for t in templates]
    return PaginatedSiteTemplates(total=total, page=page, page_size=page_size, items=items)


@router.get("/all", response_model=list[SiteTemplateOut])
def list_all_active_templates(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """获取所有启用的模板(不分页，用于创建微站时选择)"""
    templates = db.query(SiteTemplate).filter(SiteTemplate.status == "active").order_by(SiteTemplate.sort_order.asc(), SiteTemplate.id.desc()).all()
    return [_to_out(t) for t in templates]


@router.get("/{template_id}", response_model=SiteTemplateOut)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """模板详情"""
    tpl = db.query(SiteTemplate).filter(SiteTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="模板不存在")
    return _to_out(tpl)


@router.post("", response_model=SiteTemplateOut)
def create_template(
    req: SiteTemplateCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """创建模板（仅管理员）"""
    if not _can_manage_templates(current):
        raise HTTPException(status_code=403, detail="无权管理模板")
    tpl = SiteTemplate(
        name=req.name,
        description=req.description,
        template_key=req.template_key,
        layout=req.layout,
        kv_image=req.kv_image,
        title_config=json.dumps(req.title_config, ensure_ascii=False) if req.title_config else None,
        background_color=req.background_color,
        background_image=req.background_image,
        share_image=req.share_image,
        share_title=req.share_title,
        share_subtitle=req.share_subtitle,
        preview_image=req.preview_image,
        modules_config=json.dumps(req.modules_config, ensure_ascii=False) if req.modules_config else None,
        status=req.status,
        sort_order=req.sort_order,
        created_by=current.id,
    )
    try:
        db.add(tpl)
        db.commit()
        db.refresh(tpl)
    except Exception as e:
        db.rollback()
        logger.error(f"创建模板失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")
    return _to_out(tpl)


@router.put("/{template_id}", response_model=SiteTemplateOut)
def update_template(
    template_id: int,
    req: SiteTemplateUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """更新模板（仅管理员，系统模板的 template_key 不可改）"""
    if not _can_manage_templates(current):
        raise HTTPException(status_code=403, detail="无权管理模板")
    tpl = db.query(SiteTemplate).filter(SiteTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="模板不存在")
    for field, value in req.model_dump(exclude_unset=True).items():
        if field in ("modules_config", "title_config"):
            value = json.dumps(value, ensure_ascii=False) if value else None
        setattr(tpl, field, value)
    try:
        db.commit()
        db.refresh(tpl)
    except Exception as e:
        db.rollback()
        logger.error(f"更新模板失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
    return _to_out(tpl)


@router.delete("/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """删除模板（仅管理员，系统模板不可删除）"""
    if not _can_manage_templates(current):
        raise HTTPException(status_code=403, detail="无权管理模板")
    tpl = db.query(SiteTemplate).filter(SiteTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="模板不存在")
    if tpl.is_system:
        raise HTTPException(status_code=400, detail="系统内置模板不可删除")
    try:
        db.delete(tpl)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"删除模板失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
    return {"message": "已删除"}
