"""会员与计费模型"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def _utcnow() -> datetime:
    """与现有模型一致的 UTC naive 时间"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class MembershipPlan(Base):
    """会员套餐表（含会员套餐和场次额度单价两种类型）"""
    __tablename__ = "membership_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="套餐名称")
    plan_type = Column(String(20), nullable=False, comment="套餐类型: membership/session_credit")
    price = Column(Integer, nullable=False, default=0, comment="价格(分)")
    duration_days = Column(Integer, nullable=True, comment="时长(天), membership类型使用")
    credit_quantity = Column(Integer, nullable=True, comment="额度数量, session_credit类型使用")
    description = Column(String(500), nullable=True, comment="描述")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    created_at = Column(DateTime, default=_utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, comment="更新时间")


class Membership(Base):
    """会员记录表"""
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    plan_id = Column(Integer, ForeignKey("membership_plans.id"), nullable=False, comment="套餐ID")
    transaction_id = Column(Integer, ForeignKey("wallet_transactions.id"), nullable=True, comment="关联流水ID")
    start_at = Column(DateTime, nullable=False, comment="会员开始时间")
    end_at = Column(DateTime, nullable=False, comment="会员到期时间")
    status = Column(String(20), default="active", nullable=False, comment="状态: active/expired/refunded")
    created_at = Column(DateTime, default=_utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, comment="更新时间")

    user = relationship("User", backref="memberships")
    plan = relationship("MembershipPlan")
