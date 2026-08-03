"""账号管理路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, SiteAccount, AccountModulePermission, Module, Site
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.deps import get_current_admin
from app.schemas.account import (
    AccountImportRequest, AccountUpdate, AccountOut,
    PaginatedAccounts, AccountPermissionUpdate,
)

router = APIRouter(prefix="/sites/{site_id}/accounts", tags=["账号管理"])


def _get_site_or_404(db: Session, site_id: int) -> Site:
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")
    return site


def _account_to_out(acc: SiteAccount) -> AccountOut:
    return AccountOut(
        id=acc.id,
        site_id=acc.site_id,
        username=acc.username,
        nickname=acc.nickname,
        phone=acc.phone,
        is_active=acc.is_active,
        created_at=acc.created_at,
        updated_at=acc.updated_at,
        permitted_module_ids=[p.module_id for p in acc.permissions],
    )


@router.get("", response_model=PaginatedAccounts)
def list_accounts(
    site_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    keyword: str | None = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """账号列表"""
    _get_site_or_404(db, site_id)
    q = db.query(SiteAccount).filter(SiteAccount.site_id == site_id)
    if keyword:
        q = q.filter(
            (SiteAccount.username.like(f"%{keyword}%"))
            | (SiteAccount.nickname.like(f"%{keyword}%"))
            | (SiteAccount.phone.like(f"%{keyword}%"))
        )
    total = q.count()
    accounts = q.order_by(SiteAccount.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedAccounts(
        total=total, page=page, page_size=page_size,
        items=[_account_to_out(a) for a in accounts],
    )


@router.post("/import", response_model=dict)
def import_accounts(
    site_id: int,
    req: AccountImportRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """批量导入账号"""
    _get_site_or_404(db, site_id)
    created = 0
    skipped = 0
    for item in req.accounts:
        existing = db.query(SiteAccount).filter(
            SiteAccount.site_id == site_id,
            SiteAccount.username == item.username,
        ).first()
        if existing:
            # 已存在则更新密码
            existing.password_hash = hash_password(item.password)
            if item.nickname:
                existing.nickname = item.nickname
            if item.phone:
                existing.phone = item.phone
            skipped += 1
        else:
            acc = SiteAccount(
                site_id=site_id,
                username=item.username,
                password_hash=hash_password(item.password),
                nickname=item.nickname,
                phone=item.phone,
            )
            db.add(acc)
            created += 1
    db.commit()
    return {"message": f"导入完成: 新增{created}个, 更新{skipped}个", "created": created, "updated": skipped}


@router.put("/{account_id}", response_model=AccountOut)
def update_account(
    site_id: int,
    account_id: int,
    req: AccountUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """更新账号"""
    acc = db.query(SiteAccount).filter(
        SiteAccount.id == account_id, SiteAccount.site_id == site_id
    ).first()
    if not acc:
        raise HTTPException(status_code=404, detail="账号不存在")
    if req.password:
        acc.password_hash = hash_password(req.password)
    if req.nickname is not None:
        acc.nickname = req.nickname
    if req.phone is not None:
        acc.phone = req.phone
    if req.is_active is not None:
        acc.is_active = req.is_active
    db.commit()
    db.refresh(acc)
    return _account_to_out(acc)


@router.delete("/{account_id}")
def delete_account(
    site_id: int,
    account_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """删除账号"""
    acc = db.query(SiteAccount).filter(
        SiteAccount.id == account_id, SiteAccount.site_id == site_id
    ).first()
    if not acc:
        raise HTTPException(status_code=404, detail="账号不存在")
    db.delete(acc)
    db.commit()
    return {"message": "已删除"}


@router.put("/{account_id}/permissions", response_model=AccountOut)
def update_permissions(
    site_id: int,
    account_id: int,
    req: AccountPermissionUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """设置账号可访问的模块权限"""
    acc = db.query(SiteAccount).filter(
        SiteAccount.id == account_id, SiteAccount.site_id == site_id
    ).first()
    if not acc:
        raise HTTPException(status_code=404, detail="账号不存在")

    # 删除旧权限
    db.query(AccountModulePermission).filter(
        AccountModulePermission.account_id == account_id
    ).delete()

    # 新增新权限(校验module属于该site)
    for module_id in req.module_ids:
        module = db.query(Module).filter(
            Module.id == module_id, Module.site_id == site_id
        ).first()
        if module:
            perm = AccountModulePermission(account_id=account_id, module_id=module_id)
            db.add(perm)

    db.commit()
    db.refresh(acc)
    return _account_to_out(acc)
