"""依赖注入: 认证、数据库等"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import decode_access_token
from app.models import User, SiteAccount

security_scheme = HTTPBearer(auto_error=False)


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
    return user


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
