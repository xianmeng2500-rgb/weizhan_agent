"""认证路由 - 后台管理员登录与账号管理"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.utils.security import verify_password, create_access_token, hash_password
from app.utils.deps import (
    get_current_admin,
    can_manage_accounts,
    can_manage_target_role,
    ROLE_SUPER_ADMIN,
    ROLE_ADMIN,
    ROLE_SUB_ADMIN,
)
from app.schemas.auth import (
    LoginRequest, TokenResponse, UserInfo,
    AdminUserCreate, AdminUserUpdate, AdminUserOut,
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """管理员登录"""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )
    token = create_access_token(subject=str(user.id), token_type="admin")
    return TokenResponse(
        access_token=token,
        nickname=user.nickname or user.username,
        role=user.role,
    )


@router.get("/me", response_model=UserInfo)
def me(current: User = Depends(get_current_admin)):
    """获取当前管理员信息"""
    return UserInfo.model_validate(current)


@router.post("/logout")
def logout(current: User = Depends(get_current_admin)):
    """退出登录(JWT无状态, 前端丢弃token即可)"""
    return {"message": "已退出登录"}


# ---------------- 后台账号管理 ----------------

@router.get("/accounts", response_model=list[AdminUserOut])
def list_accounts(
    keyword: str | None = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """后台账号列表

    - 超级管理员: 查看所有账号(排除自己, 避免误操作)
    - 管理员: 仅查看自己创建的子账号
    - 子账号: 无权限
    """
    if not can_manage_accounts(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权管理账号")

    q = db.query(User)
    if current.role == ROLE_SUPER_ADMIN:
        q = q.filter(User.id != current.id)
    elif current.role == ROLE_ADMIN:
        q = q.filter(User.created_by == current.id, User.role == ROLE_SUB_ADMIN)
    if keyword:
        q = q.filter(
            (User.username.like(f"%{keyword}%")) | (User.nickname.like(f"%{keyword}%"))
        )
    users = q.order_by(User.created_at.desc()).all()
    return [AdminUserOut.model_validate(u) for u in users]


@router.post("/accounts", response_model=AdminUserOut)
def create_account(
    req: AdminUserCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """创建后台账号

    - 超级管理员: 可创建任意角色
    - 管理员: 只能创建子账号(sub_admin), 且归属自己
    - 子账号: 无权限
    """
    if not can_manage_accounts(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权管理账号")
    if req.role not in (ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_SUB_ADMIN):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的角色")
    if not can_manage_target_role(current, req.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您无权创建该角色的账号",
        )
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")

    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        nickname=req.nickname,
        role=req.role,
        is_active=True,
        created_by=current.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return AdminUserOut.model_validate(user)


@router.get("/accounts/{user_id}", response_model=AdminUserOut)
def get_account(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """账号详情"""
    if not can_manage_accounts(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权管理账号")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账号不存在")
    _check_account_scope(user, current)
    return AdminUserOut.model_validate(user)


@router.put("/accounts/{user_id}", response_model=AdminUserOut)
def update_account(
    user_id: int,
    req: AdminUserUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """编辑账号(改密码/昵称/角色/启用状态)"""
    if not can_manage_accounts(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权管理账号")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账号不存在")
    _check_account_scope(user, current)

    # 角色变更需校验权限
    if req.role is not None and req.role != user.role:
        if req.role not in (ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_SUB_ADMIN):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的角色")
        if not can_manage_target_role(current, req.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您无权将该账号设置为该角色",
            )
        user.role = req.role

    if req.password:
        user.password_hash = hash_password(req.password)
    if req.nickname is not None:
        user.nickname = req.nickname
    if req.is_active is not None:
        # 不能禁用自己
        if user.id == current.id and not req.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能禁用当前登录账号")
        user.is_active = req.is_active

    db.commit()
    db.refresh(user)
    return AdminUserOut.model_validate(user)


@router.delete("/accounts/{user_id}")
def delete_account(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """删除账号"""
    if not can_manage_accounts(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权管理账号")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账号不存在")
    _check_account_scope(user, current)

    if user.id == current.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除当前登录账号")
    if user.role == ROLE_SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="不能删除超级管理员")

    db.delete(user)
    db.commit()
    return {"message": "已删除"}


def _check_account_scope(user: User, current: User):
    """校验 current 是否有权操作 user 账号"""
    if current.role == ROLE_SUPER_ADMIN:
        return
    if current.role == ROLE_ADMIN:
        # 管理员只能操作自己创建的子账号
        if user.created_by != current.id or user.role != ROLE_SUB_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该账号")
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该账号")
