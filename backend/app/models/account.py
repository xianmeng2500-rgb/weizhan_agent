"""登录账号与权限模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class SiteAccount(Base):
    """微站前端登录账号"""
    __tablename__ = "site_accounts"
    __table_args__ = (
        UniqueConstraint("site_id", "username", name="uk_site_username"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True, comment="所属微站")
    username = Column(String(64), nullable=False, comment="登录账号")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    nickname = Column(String(64), nullable=True, comment="昵称")
    phone = Column(String(20), nullable=True, comment="手机号")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    site = relationship("Site", back_populates="accounts")
    permissions = relationship("AccountModulePermission", back_populates="account", cascade="all, delete-orphan")


class AccountModulePermission(Base):
    """账号-模块权限关系"""
    __tablename__ = "account_module_permissions"
    __table_args__ = (
        UniqueConstraint("account_id", "module_id", name="uk_account_module"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("site_accounts.id"), nullable=False, index=True, comment="账号ID")
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False, index=True, comment="模块ID")

    # 关系
    account = relationship("SiteAccount", back_populates="permissions")
    module = relationship("Module", back_populates="permissions")
