"""认证路由 - 后台管理员登录"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.utils.security import verify_password, create_access_token
from app.utils.deps import get_current_admin
from app.schemas.auth import LoginRequest, TokenResponse, UserInfo

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
    token = create_access_token(subject=str(user.id), token_type="admin")
    return TokenResponse(access_token=token, nickname=user.nickname or user.username)


@router.get("/me", response_model=UserInfo)
def me(current: User = Depends(get_current_admin)):
    """获取当前管理员信息"""
    return UserInfo.model_validate(current)


@router.post("/logout")
def logout(current: User = Depends(get_current_admin)):
    """退出登录(JWT无状态, 前端丢弃token即可)"""
    return {"message": "已退出登录"}
