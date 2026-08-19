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
    # 商业化: 钱包与会员缓存字段
    wallet_balance = Column(Integer, default=0, nullable=False, comment="钱包余额(分)")
    membership_status = Column(String(20), default="none", nullable=False, comment="会员状态缓存: active/expired/none")
    membership_end_at = Column(DateTime, nullable=True, comment="会员到期时间缓存")
    session_credit_balance = Column(Integer, default=0, nullable=False, comment="场次额度余额缓存")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")
