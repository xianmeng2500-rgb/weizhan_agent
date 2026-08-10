"""后台管理员模型"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.database import Base


class User(Base):
    """后台管理员"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, index=True, nullable=False, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    nickname = Column(String(64), nullable=True, comment="昵称")
    role = Column(String(20), default="sub_admin", nullable=False, comment="角色: super_admin/admin/sub_admin")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建者(上级管理员)")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")
