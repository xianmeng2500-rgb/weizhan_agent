"""签到系统模型"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


def _utcnow() -> datetime:
    """与现有模型一致的 UTC naive 时间"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CheckinConfig(Base):
    """签到配置表（每个微站一条，与 sites.need_checkin 联动）。
    多场次上线后时间窗移至 checkin_sessions，此表仅保留站点级开关与默认值。"""
    __tablename__ = "checkin_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True, comment="微站ID")
    checkin_start_at = Column(DateTime, nullable=True, comment="[已废弃] 站点级开始时间，迁移至场次")
    checkin_end_at = Column(DateTime, nullable=True, comment="[已废弃] 站点级结束时间，迁移至场次")
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="最后修改人(管理员ID)")
    created_at = Column(DateTime, default=_utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, comment="更新时间")

    site = relationship("Site", backref="checkin_config")

    __table_args__ = (
        UniqueConstraint("site_id", name="uk_checkin_config_site"),
    )


class CheckinSession(Base):
    """签到场次表（一个微站可配置多场签到）"""
    __tablename__ = "checkin_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True, comment="微站ID")
    name = Column(String(64), nullable=False, comment="场次名称，如：上午场、下午场、Day1")
    start_at = Column(DateTime, nullable=True, comment="签到开始时间，NULL表示不限制")
    end_at = Column(DateTime, nullable=True, comment="签到结束时间，NULL表示不限制")
    enabled = Column(Boolean, default=True, nullable=False, comment="是否启用: 1启用 0停用")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序，从小到大")
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="最后修改人")
    created_at = Column(DateTime, default=_utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, comment="更新时间")

    site = relationship("Site", backref="checkin_sessions")


class CheckinRecord(Base):
    """签到记录表（同一微站同一账号同一场次仅一条有效记录）"""
    __tablename__ = "checkin_records"
    __table_args__ = (
        UniqueConstraint("site_id", "account_id", "session_id", name="uk_checkin_site_account_session"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True, comment="微站ID")
    account_id = Column(Integer, ForeignKey("site_accounts.id"), nullable=False, index=True, comment="微站登录账号ID")
    session_id = Column(Integer, ForeignKey("checkin_sessions.id"), nullable=True, index=True, comment="签到场次ID")
    checkin_status = Column(Boolean, default=True, nullable=False, comment="签到状态: 1有效 0已撤销")
    checkin_at = Column(DateTime, nullable=False, comment="签到时间")
    checkin_method = Column(String(16), default="QR_SCAN", nullable=False, comment="签到方式: QR_SCAN/MANUAL")
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="操作人(后台管理员ID)")
    operator_name = Column(String(64), nullable=True, comment="操作人姓名快照")
    remark = Column(Text, nullable=True, comment="备注(补签/撤销原因)")
    created_at = Column(DateTime, default=_utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, comment="更新时间")

    # 关系
    site = relationship("Site", backref="checkin_records")
    account = relationship("SiteAccount", backref="checkin_records")
    session = relationship("CheckinSession", backref="records")
