"""微站管理路由"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Site, SiteTemplate, Module
from app.utils.deps import get_current_admin, assert_site_access, ROLE_SUPER_ADMIN
from app.services.billing_service import assert_active_membership, consume_credit_for_site_online
from app.schemas.site import (
    SiteCreate, SiteUpdate, SiteStatusUpdate,
    SiteOut, PaginatedSites,
)
from app.schemas.module import ModuleOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sites", tags=["微站管理"])

# 模板外观字段: 创建微站时若未显式提供则继承模板值
# 映射为 site字段 -> (模板字段, 站点默认值)
_TEMPLATE_APPEARANCE_FIELDS = {
    "template": ("template_key", "default"),
    "layout": ("layout", "grid"),
    "kv_image": ("kv_image", None),
    "background_color": ("background_color", None),
    "background_image": ("background_image", None),
    "share_image": ("share_image", None),
    "share_title": ("share_title", None),
    "share_subtitle": ("share_subtitle", None),
}

# 模块可复制字段（用于从模板 modules_config 创建预置模块）
_MODULE_FIELDS = (
    "title", "icon", "sort_order", "content_type", "external_url", "rich_content",
    "form_config", "schedule_config", "qrcode_config", "is_active",
    "position_x", "position_y", "width", "height", "border_radius",
    "bg_color", "font_color", "icon_position", "content_align", "show_arrow",
)


def _service_config(site: Site) -> dict:
    """将数据库中的客服配置 JSON 安全转换为字典。"""
    if not site.customer_service_config:
        return {}
    try:
        return json.loads(site.customer_service_config)
    except (TypeError, json.JSONDecodeError):
        return {}


def _login_fields_config(site: Site) -> list[dict]:
    """将数据库中的登录字段配置 JSON 安全转换为列表。"""
    if not site.login_fields_config:
        return [{"key": "username", "display_name": "账号", "type": "text"}]
    try:
        return json.loads(site.login_fields_config)
    except (TypeError, json.JSONDecodeError):
        return [{"key": "username", "display_name": "账号", "type": "text"}]


def _login_form_config(site: Site) -> dict:
    """将数据库中的登录表单配置 JSON 安全转换为字典。"""
    if not site.login_form_config:
        return {"position": "center"}
    try:
        return json.loads(site.login_form_config)
    except (TypeError, json.JSONDecodeError):
        return {"position": "center"}


def _title_config(site: Site) -> dict | None:
    """将数据库中的微站标题配置 JSON 安全转换为字典。"""
    if not site.title_config:
        return None
    try:
        return json.loads(site.title_config)
    except (TypeError, json.JSONDecodeError):
        return None


def _to_out(site: Site, db: Session) -> SiteOut:
    """转换模型为输出Schema(带统计)"""
    return SiteOut(
        id=site.id,
        name=site.name,
        code=site.code,
        template=site.template,
        layout=site.layout,
        kv_image=site.kv_image,
        title_config=_title_config(site),
        background_color=site.background_color,
        background_image=site.background_image,
        share_image=site.share_image,
        share_title=site.share_title,
        share_subtitle=site.share_subtitle,
        customer_service_config=_service_config(site),
        login_fields_config=_login_fields_config(site),
        login_form_config=_login_form_config(site),
        grid_offset_y=site.grid_offset_y,
        need_login=site.need_login,
        login_require_password=site.login_require_password,
        need_checkin=site.need_checkin,
        start_time=site.start_time,
        end_time=site.end_time,
        status=site.status,
        close_message=site.close_message,
        created_by=site.created_by,
        created_at=site.created_at,
        updated_at=site.updated_at,
        module_count=len(site.modules),
        account_count=len(site.accounts),
    )


@router.get("", response_model=PaginatedSites)
def list_sites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """微站列表(分页)"""
    q = db.query(Site)
    # 非超级管理员仅能看到自己创建的微站
    if current.role != ROLE_SUPER_ADMIN:
        q = q.filter(Site.created_by == current.id)
    if status:
        q = q.filter(Site.status == status)
    if keyword:
        q = q.filter(Site.name.like(f"%{keyword}%"))
    total = q.count()
    sites = q.order_by(Site.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [_to_out(s, db) for s in sites]
    return PaginatedSites(total=total, page=page, page_size=page_size, items=items)


@router.post("", response_model=SiteOut)
def create_site(
    req: SiteCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """创建微站(支持传入 template_id 套用模板)"""
    # 商业化: 校验会员状态（sub_admin 继承父账号）
    assert_active_membership(db, current)
    # 检查code唯一性
    if db.query(Site).filter(Site.code == req.code).first():
        raise HTTPException(status_code=400, detail="微站唯一码已存在")

    # 套用模板: 未显式提供的外观字段继承模板值
    req_data = req.model_dump(exclude_unset=True)
    tpl = None
    if req.template_id:
        tpl = db.query(SiteTemplate).filter(
            SiteTemplate.id == req.template_id, SiteTemplate.status == "active"
        ).first()
        if not tpl:
            raise HTTPException(status_code=404, detail="模板不存在或未启用")

    def _appearance(field: str, tpl_field: str, default):
        """优先使用请求显式提供的值，否则回退模板值，最后取默认值"""
        if field in req_data and req_data[field] not in (None, ""):
            return req_data[field]
        if tpl:
            tpl_value = getattr(tpl, tpl_field)
            if tpl_value not in (None, ""):
                return tpl_value
        return default

    site_kwargs = {
        field: _appearance(field, tpl_field, default)
        for field, (tpl_field, default) in _TEMPLATE_APPEARANCE_FIELDS.items()
    }

    # 标题装饰配置: 请求显式提供优先，否则继承模板（模板中为 JSON 文本，需解析）
    title_cfg = req.title_config
    if not title_cfg and tpl and tpl.title_config:
        try:
            title_cfg = json.loads(tpl.title_config)
        except (TypeError, json.JSONDecodeError):
            title_cfg = None

    site = Site(
        name=req.name,
        code=req.code,
        **site_kwargs,
        title_config=json.dumps(title_cfg, ensure_ascii=False) if title_cfg else None,
        customer_service_config=json.dumps(req.customer_service_config, ensure_ascii=False) if req.customer_service_config else None,
        login_fields_config=json.dumps(req.login_fields_config, ensure_ascii=False) if req.login_fields_config else None,
        login_form_config=json.dumps(req.login_form_config, ensure_ascii=False) if req.login_form_config else None,
        need_login=req.need_login,
        login_require_password=req.login_require_password,
        start_time=req.start_time,
        end_time=req.end_time,
        close_message=req.close_message,
        created_by=current.id,
    )
    try:
        db.add(site)
        db.flush()
        # 从模板创建预置模块
        if tpl and tpl.modules_config:
            try:
                presets = json.loads(tpl.modules_config)
                for item in presets:
                    if not isinstance(item, dict) or not item.get("title"):
                        continue
                    db.add(Module(
                        site_id=site.id,
                        **{k: item[k] for k in _MODULE_FIELDS if k in item},
                    ))
            except (TypeError, json.JSONDecodeError):
                logger.warning(f"模板 {tpl.id} 的 modules_config 解析失败，跳过预置模块")
        db.commit()
        db.refresh(site)
    except Exception as e:
        db.rollback()
        logger.error(f"创建微站失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")
    return _to_out(site, db)


@router.get("/{site_id}", response_model=SiteOut)
def get_site(
    site_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """微站详情"""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")
    assert_site_access(site, current)
    return _to_out(site, db)


@router.put("/{site_id}", response_model=SiteOut)
def update_site(
    site_id: int,
    req: SiteUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """更新微站"""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")
    assert_site_access(site, current)
    # 商业化: 校验会员状态（过期后微站只读）
    assert_active_membership(db, current)
    if req.code and req.code != site.code:
        if site.status == "online":
            raise HTTPException(status_code=400, detail="微站已上线，访问码不可修改")
        if db.query(Site).filter(Site.code == req.code).first():
            raise HTTPException(status_code=400, detail="微站唯一码已存在")
    for field, value in req.model_dump(exclude_unset=True).items():
        if field in ("customer_service_config", "login_form_config", "title_config"):
            value = json.dumps(value, ensure_ascii=False) if value else None
        elif field == "login_fields_config":
            value = json.dumps(value, ensure_ascii=False) if value else None
        setattr(site, field, value)
    try:
        db.commit()
        db.refresh(site)
    except Exception as e:
        db.rollback()
        logger.error(f"更新微站失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
    return _to_out(site, db)


@router.delete("/{site_id}")
def delete_site(
    site_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """删除微站"""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")
    assert_site_access(site, current)
    try:
        db.delete(site)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"删除微站失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
    return {"message": "已删除"}


@router.put("/{site_id}/status", response_model=SiteOut)
def update_status(
    site_id: int,
    req: SiteStatusUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """更新微站状态(上线/下线)"""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")
    assert_site_access(site, current)
    if req.status not in ("draft", "online", "offline"):
        raise HTTPException(status_code=400, detail="无效状态")
    # 商业化(v1.2): 每次上线扣减1个场次额度（super_admin 免费）；下线不退额度
    if req.status == "online" and site.status != "online" and current.role != ROLE_SUPER_ADMIN:
        try:
            consume_credit_for_site_online(db, current, site.id)
        except ValueError:
            raise HTTPException(
                status_code=403,
                detail="CREDIT_INSUFFICIENT:场次额度不足，无法上线。请前往会员中心购买（299元/次）",
            )
    site.status = req.status
    try:
        db.commit()
        db.refresh(site)
    except Exception as e:
        db.rollback()
        logger.error(f"更新微站状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
    return _to_out(site, db)
