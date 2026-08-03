"""后台管理员模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base


class User(Base):
    """后台管理员"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, index=True, nullable=False, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    nickname = Column(String(64), nullable=True, comment="昵称")
    role = Column(String(20), default="admin", nullable=False, comment="角色: admin/editor")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
