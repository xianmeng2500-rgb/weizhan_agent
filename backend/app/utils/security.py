"""安全工具: JWT + 密码哈希"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt
import bcrypt
from app.config import settings


def hash_password(password: str) -> str:
    """生成密码哈希 (bcrypt)"""
    pwd_bytes = password.encode("utf-8")
    # bcrypt 限制密码最长 72 字节，截断处理
    if len(pwd_bytes) > 72:
        pwd_bytes = pwd_bytes[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码与哈希是否匹配"""
    pwd_bytes = plain_password.encode("utf-8")
    if len(pwd_bytes) > 72:
        pwd_bytes = pwd_bytes[:72]
    try:
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(
    subject: str,
    extra_claims: Optional[Dict[str, Any]] = None,
    expires_minutes: Optional[int] = None,
    token_type: str = "admin",
) -> str:
    """生成JWT Token

    Args:
        subject: 主体标识 (user_id 或 account_id)
        extra_claims: 额外声明
        expires_minutes: 过期时间(分钟)
        token_type: admin(后台) / frontend(前端)
    """
    if expires_minutes is None:
        expires_minutes = (
            settings.JWT_EXPIRE_MINUTES if token_type == "admin" else settings.JWT_FRONTEND_EXPIRE_MINUTES
        )
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload: Dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "type": token_type,
        "iat": datetime.now(timezone.utc),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """解码JWT Token"""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except Exception:
        return None
