"""场次额度模型"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SessionCredit(Base):
    """场次额度表（每条记录=1次上线额度，购买后1年有效）"""
    __tablename__ = "session_credits"
    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
        Index("idx_expire", "expire_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    transaction_id = Column(Integer, ForeignKey("wallet_transactions.id"), nullable=True, comment="关联流水ID")
    session_id = Column(Integer, ForeignKey("checkin_sessions.id"), nullable=True, comment="(废弃)历史字段:曾关联签到场次")
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=True, comment="使用后关联的微站ID(上线扣减)")
    status = Column(String(20), default="unused", nullable=False, comment="状态: unused/used/expired/refunded")
    expire_at = Column(DateTime, nullable=False, comment="到期时间(购买后+365天)")
    used_at = Column(DateTime, nullable=True, comment="使用时间")
    created_at = Column(DateTime, default=_utcnow, comment="购买时间")

    user = relationship("User", backref="session_credits")
    session = relationship("CheckinSession")
    site = relationship("Site", back_populates="session_credits")
