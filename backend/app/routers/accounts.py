"""账号管理路由"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, SiteAccount, AccountModulePermission, Module, Site
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.deps import get_current_admin, assert_site_access
from app.services.billing_service import assert_active_membership
from app.services.site_limits import get_site_limits
from app.schemas.account import (
    AccountImportRequest, AccountCreate, AccountUpdate, AccountOut,
    PaginatedAccounts, AccountPermissionUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sites/{site_id}/accounts", tags=["账号管理"])


def _get_site_or_404(db: Session, site_id: int, current: User, require_membership: bool = False) -> Site:
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")
    assert_site_access(site, current)
    # 商业化: 写操作校验会员状态（过期后微站只读）
    if require_membership:
        assert_active_membership(db, current)
    return site


def _account_to_out(acc: SiteAccount) -> AccountOut:
    custom_fields = None
    if acc.custom_fields:
        try:
            custom_fields = json.loads(acc.custom_fields)
        except (TypeError, json.JSONDecodeError):
            custom_fields = None
    return AccountOut(
        id=acc.id,
        site_id=acc.site_id,
        username=acc.username,
        nickname=acc.nickname,
        phone=acc.phone,
        custom_fields=custom_fields,
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
    _get_site_or_404(db, site_id, current)
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


@router.post("", response_model=AccountOut)
def create_account(
    site_id: int,
    req: AccountCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """创建单个账号"""
    _get_site_or_404(db, site_id, current, require_membership=True)
    # 校验账号数量上限
    max_accounts, _ = get_site_limits(db)
    current_total = db.query(SiteAccount).filter(SiteAccount.site_id == site_id).count()
    if current_total >= max_accounts:
        raise HTTPException(
            status_code=400,
            detail=f"该微站登录账号数量已达上限（{max_accounts}），无法继续创建",
        )
    # 校验 username 唯一性
    existing = db.query(SiteAccount).filter(
        SiteAccount.site_id == site_id,
        SiteAccount.username == req.username,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="账号已存在")
    acc = SiteAccount(
        site_id=site_id,
        username=req.username,
        password_hash=hash_password(req.password) if req.password else "",
        nickname=req.nickname,
        phone=req.phone,
        custom_fields=json.dumps(req.custom_fields, ensure_ascii=False) if req.custom_fields else None,
    )
    try:
        db.add(acc)
        db.commit()
        db.refresh(acc)
    except Exception as e:
        db.rollback()
        logger.error(f"创建账号失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")
    return _account_to_out(acc)


@router.post("/import", response_model=dict)
def import_accounts(
    site_id: int,
    req: AccountImportRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """批量导入账号"""
    _get_site_or_404(db, site_id, current, require_membership=True)
    # 校验账号数量上限：现有账号 + 本次将新增的账号 <= 上限
    max_accounts, _ = get_site_limits(db)
    existing_usernames = {
        row[0] for row in db.query(SiteAccount.username).filter(SiteAccount.site_id == site_id).all()
    }
    seen = set()
    to_create = 0
    for item in req.accounts:
        if item.username not in existing_usernames and item.username not in seen:
            to_create += 1
        seen.add(item.username)
    if len(existing_usernames) + to_create > max_accounts:
        remaining = max_accounts - len(existing_usernames)
        raise HTTPException(
            status_code=400,
            detail=f"该微站登录账号数量已达上限（{max_accounts}），当前仅可再新增 {remaining} 个，请调整导入名单",
        )
    created = 0
    skipped = 0
    try:
        for item in req.accounts:
            existing = db.query(SiteAccount).filter(
                SiteAccount.site_id == site_id,
                SiteAccount.username == item.username,
            ).first()
            if existing:
                # 已存在则更新密码
                if item.password:
                    existing.password_hash = hash_password(item.password)
                if item.nickname:
                    existing.nickname = item.nickname
                if item.phone:
                    existing.phone = item.phone
                if item.custom_fields:
                    existing.custom_fields = json.dumps(item.custom_fields, ensure_ascii=False)
                skipped += 1
            else:
                acc = SiteAccount(
                    site_id=site_id,
                    username=item.username,
                    password_hash=hash_password(item.password) if item.password else "",
                    nickname=item.nickname,
                    phone=item.phone,
                    custom_fields=json.dumps(item.custom_fields, ensure_ascii=False) if item.custom_fields else None,
                )
                db.add(acc)
                created += 1
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"导入账号失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
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
    assert_active_membership(db, current)
    acc = db.query(SiteAccount).filter(
        SiteAccount.id == account_id, SiteAccount.site_id == site_id
    ).first()
    if not acc:
        raise HTTPException(status_code=404, detail="账号不存在")
    if req.username is not None and req.username != acc.username:
        # 校验新 username 唯一性
        dup = db.query(SiteAccount).filter(
            SiteAccount.site_id == site_id,
            SiteAccount.username == req.username,
        ).first()
        if dup:
            raise HTTPException(status_code=400, detail="账号已存在")
        acc.username = req.username
    if req.password:
        acc.password_hash = hash_password(req.password)
    if req.nickname is not None:
        acc.nickname = req.nickname
    if req.phone is not None:
        acc.phone = req.phone
    if req.custom_fields is not None:
        acc.custom_fields = json.dumps(req.custom_fields, ensure_ascii=False)
    if req.is_active is not None:
        acc.is_active = req.is_active
    try:
        db.commit()
        db.refresh(acc)
    except Exception as e:
        db.rollback()
        logger.error(f"更新账号失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
    return _account_to_out(acc)


@router.delete("/{account_id}")
def delete_account(
    site_id: int,
    account_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """删除账号"""
    assert_active_membership(db, current)
    acc = db.query(SiteAccount).filter(
        SiteAccount.id == account_id, SiteAccount.site_id == site_id
    ).first()
    if not acc:
        raise HTTPException(status_code=404, detail="账号不存在")
    try:
        db.delete(acc)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"删除账号失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
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
    assert_active_membership(db, current)
    acc = db.query(SiteAccount).filter(
        SiteAccount.id == account_id, SiteAccount.site_id == site_id
    ).first()
    if not acc:
        raise HTTPException(status_code=404, detail="账号不存在")

    try:
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
    except Exception as e:
        db.rollback()
        logger.error(f"更新权限失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新权限失败: {str(e)}")
    return _account_to_out(acc)
