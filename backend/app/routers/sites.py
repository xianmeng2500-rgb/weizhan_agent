"""微站管理路由"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Site
from app.utils.deps import get_current_admin
from app.schemas.site import (
    SiteCreate, SiteUpdate, SiteStatusUpdate,
    SiteOut, PaginatedSites,
)
from app.schemas.module import ModuleOut

router = APIRouter(prefix="/sites", tags=["微站管理"])


def _to_out(site: Site, db: Session) -> SiteOut:
    """转换模型为输出Schema(带统计)"""
    return SiteOut(
        id=site.id,
        name=site.name,
        code=site.code,
        template=site.template,
        layout=site.layout,
        kv_image=site.kv_image,
        background_color=site.background_color,
        need_login=site.need_login,
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
    """创建微站"""
    # 检查code唯一性
    if db.query(Site).filter(Site.code == req.code).first():
        raise HTTPException(status_code=400, detail="微站唯一码已存在")
    site = Site(
        name=req.name,
        code=req.code,
        template=req.template,
        layout=req.layout,
        kv_image=req.kv_image,
        background_color=req.background_color,
        need_login=req.need_login,
        start_time=req.start_time,
        end_time=req.end_time,
        close_message=req.close_message,
        created_by=current.id,
    )
    db.add(site)
    db.commit()
    db.refresh(site)
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
    if req.code and req.code != site.code:
        if db.query(Site).filter(Site.code == req.code).first():
            raise HTTPException(status_code=400, detail="微站唯一码已存在")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(site, field, value)
    db.commit()
    db.refresh(site)
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
    db.delete(site)
    db.commit()
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
    if req.status not in ("draft", "online", "offline"):
        raise HTTPException(status_code=400, detail="无效状态")
    site.status = req.status
    db.commit()
    db.refresh(site)
    return _to_out(site, db)
