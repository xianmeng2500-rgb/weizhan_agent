"""微站项目模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Site(Base):
    """微站项目"""
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, comment="微站名称")
    code = Column(String(64), unique=True, index=True, nullable=False, comment="微站唯一码(用于URL)")
    template = Column(String(20), default="classic", nullable=False, comment="模板: classic/dark/festive")
    layout = Column(String(20), default="grid", nullable=False, comment="布局: grid/button")
    kv_image = Column(String(500), nullable=True, comment="KV图URL")
    background_color = Column(String(20), default="", nullable=True, comment="自定义背景色")
    need_login = Column(Boolean, default=False, nullable=False, comment="是否需要登录")
    start_time = Column(DateTime, nullable=True, comment="开启时间")
    end_time = Column(DateTime, nullable=True, comment="关闭时间")
    status = Column(String(20), default="draft", nullable=False, comment="状态: draft/online/offline")
    close_message = Column(Text, nullable=True, comment="关闭后提示文案")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建者")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    modules = relationship("Module", back_populates="site", cascade="all, delete-orphan", order_by="Module.sort_order")
    accounts = relationship("SiteAccount", back_populates="site", cascade="all, delete-orphan")
    access_logs = relationship("AccessLog", back_populates="site")
