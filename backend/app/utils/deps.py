"""依赖注入: 认证、数据库等"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import decode_access_token
from app.models import User, SiteAccount

security_scheme = HTTPBearer(auto_error=False)

# 后台管理员角色
ROLE_SUPER_ADMIN = "super_admin"
ROLE_ADMIN = "admin"
ROLE_SUB_ADMIN = "sub_admin"

# 可管理后台账号的角色
ACCOUNT_MANAGER_ROLES = {ROLE_SUPER_ADMIN, ROLE_ADMIN}


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """获取当前后台管理员 (必须携带有效JWT)"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if payload is None or payload.get("type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )
    return user


def is_super_admin(user: User) -> bool:
    return user.role == ROLE_SUPER_ADMIN


def can_manage_accounts(current: User) -> bool:
    """当前用户是否能进入后台账号管理"""
    return current.role in ACCOUNT_MANAGER_ROLES


def can_manage_target_role(current: User, target_role: str) -> bool:
    """判断 current 是否有权管理 target_role 的账号

    - 超级管理员: 可管理所有角色
    - 管理员: 只能管理子账号(sub_admin)
    - 子账号: 无权管理任何人
    """
    if current.role == ROLE_SUPER_ADMIN:
        return True
    if current.role == ROLE_ADMIN:
        return target_role == ROLE_SUB_ADMIN
    return False


def assert_site_access(site, current: User):
    """校验当前用户是否有权访问该微站

    - 超级管理员: 可访问所有微站
    - 管理员/子账号: 仅能访问自己创建的微站(created_by == current.id)
    """
    if current.role == ROLE_SUPER_ADMIN:
        return
    if site.created_by is None or site.created_by != current.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该微站",
        )


def get_optional_frontend_account(
    request: Request,
    db: Session = Depends(get_db),
) -> SiteAccount | None:
    """从请求中获取前端登录账号 (可选)"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    payload = decode_access_token(token)
    if payload is None or payload.get("type") != "frontend":
        return None
    account_id = int(payload.get("sub", 0))
    site_id = payload.get("site_id")
    account = db.query(SiteAccount).filter(
        SiteAccount.id == account_id,
        SiteAccount.is_active == True,
    ).first()
    if account and site_id and account.site_id == int(site_id):
        return account
    return None
