"""钱包流水模型"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class WalletTransaction(Base):
    """钱包流水表（充值/购买会员/购买额度/退款）"""
    __tablename__ = "wallet_transactions"
    __table_args__ = (
        Index("idx_wallet_user", "user_id"),
        Index("idx_wallet_type", "tx_type"),
        Index("idx_wallet_created", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    tx_type = Column(String(30), nullable=False, comment="交易类型: recharge/purchase_membership/purchase_credit/ai_generate/refund")
    amount = Column(Integer, nullable=False, comment="金额(分), 正数=入账, 负数=扣款")
    balance_after = Column(Integer, nullable=False, comment="交易后余额(分)")
    plan_id = Column(Integer, ForeignKey("membership_plans.id"), nullable=True, comment="关联套餐ID(购买时)")
    membership_id = Column(Integer, ForeignKey("memberships.id"), nullable=True, comment="关联会员记录ID(购买会员时)")
    session_credit_ids = Column(String(500), nullable=True, comment="关联额度ID列表(逗号分隔)")
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="操作人(充值/退款时为超管ID)")
    remark = Column(String(500), nullable=True, comment="备注")
    created_at = Column(DateTime, default=_utcnow, comment="创建时间")

    user = relationship("User", foreign_keys=[user_id], backref="wallet_transactions")
    operator = relationship("User", foreign_keys=[operator_id])
    plan = relationship("MembershipPlan")
