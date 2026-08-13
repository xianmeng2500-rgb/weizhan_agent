"""统计日志模型"""
from datetime import date, datetime, timezone
from sqlalchemy import Column, Integer, BigInteger, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class AccessLog(Base):
    """访问日志(PV/UV)"""
    __tablename__ = "access_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True, comment="微站ID")
    account_id = Column(Integer, nullable=True, index=True, comment="登录账号ID")
    ip = Column(String(64), nullable=True, comment="IP地址")
    user_agent = Column(String(500), nullable=True, comment="User-Agent")
    visit_date = Column(Date, nullable=False, index=True, comment="访问日期")
    visit_time = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), comment="访问时间")

    # 关系
    site = relationship("Site", back_populates="access_logs")


class ModuleClickLog(Base):
    """模块点击日志"""
    __tablename__ = "module_click_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True, comment="微站ID")
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False, index=True, comment="模块ID")
    account_id = Column(Integer, nullable=True, comment="账号ID")
    click_date = Column(Date, nullable=False, index=True, comment="点击日期")
    click_time = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), comment="点击时间")

    # 关系
    module = relationship("Module", back_populates="click_logs")
