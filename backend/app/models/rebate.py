"""分销返佣记录模型"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RebateRecord(Base):
    """返佣记录：被推荐账号消费后按比例返佣给推荐人（一级）"""
    __tablename__ = "rebate_records"
    __table_args__ = (
        Index("idx_rebate_distributor", "distributor_id"),
        Index("idx_rebate_customer", "customer_id"),
        Index("idx_rebate_status", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    distributor_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="推荐人(返佣接收者)")
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="被推荐人(消费账号)")
    order_type = Column(String(30), nullable=False, comment="订单类型: membership/session_credit")
    order_ref = Column(Integer, nullable=False, comment="关联购买流水ID(wallet_transactions.id)")
    order_amount = Column(Integer, nullable=False, comment="实付金额(分)")
    rebate_rate = Column(Integer, nullable=False, comment="返佣比例(百分比, 如10表示10%)")
    rebate_amount = Column(Integer, nullable=False, comment="返佣金额(分)")
    status = Column(String(20), default="settled", nullable=False, comment="状态: settled/refunded/revoked/pending_clawback")
    created_at = Column(DateTime, default=_utcnow, comment="返佣产生时间")
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, comment="更新时间")

    distributor = relationship("User", foreign_keys=[distributor_id])
    customer = relationship("User", foreign_keys=[customer_id])
