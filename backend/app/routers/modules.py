"""模块管理路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Module, Site
from app.utils.deps import get_current_admin
from app.schemas.module import (
    ModuleCreate, ModuleUpdate, ModuleOut,
    ModuleSortRequest,
)

router = APIRouter(prefix="/sites/{site_id}/modules", tags=["模块管理"])


def _get_site_or_404(db: Session, site_id: int) -> Site:
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")
    return site


@router.get("", response_model=list[ModuleOut])
def list_modules(
    site_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """模块列表"""
    _get_site_or_404(db, site_id)
    modules = db.query(Module).filter(Module.site_id == site_id).order_by(Module.sort_order).all()
    return [ModuleOut.model_validate(m) for m in modules]


@router.post("", response_model=ModuleOut)
def create_module(
    site_id: int,
    req: ModuleCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """创建模块"""
    _get_site_or_404(db, site_id)
    module = Module(site_id=site_id, **req.model_dump())
    db.add(module)
    db.commit()
    db.refresh(module)
    return ModuleOut.model_validate(module)


@router.get("/{module_id}", response_model=ModuleOut)
def get_module(
    site_id: int,
    module_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """模块详情"""
    module = db.query(Module).filter(Module.id == module_id, Module.site_id == site_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
    return ModuleOut.model_validate(module)


@router.put("/{module_id}", response_model=ModuleOut)
def update_module(
    site_id: int,
    module_id: int,
    req: ModuleUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """更新模块"""
    module = db.query(Module).filter(Module.id == module_id, Module.site_id == site_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(module, field, value)
    db.commit()
    db.refresh(module)
    return ModuleOut.model_validate(module)


@router.delete("/{module_id}")
def delete_module(
    site_id: int,
    module_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """删除模块"""
    module = db.query(Module).filter(Module.id == module_id, Module.site_id == site_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
    db.delete(module)
    db.commit()
    return {"message": "已删除"}


@router.put("/sort")
def sort_modules(
    site_id: int,
    req: ModuleSortRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """批量排序模块"""
    _get_site_or_404(db, site_id)
    for item in req.items:
        module = db.query(Module).filter(Module.id == item.module_id, Module.site_id == site_id).first()
        if module:
            module.sort_order = item.sort_order
    db.commit()
    return {"message": "排序已更新"}
