"""模块模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Module(Base):
    """微站模块(九宫格/按钮)"""
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True, comment="所属微站")
    title = Column(String(128), nullable=False, comment="模块标题")
    icon = Column(String(500), nullable=True, comment="图标URL")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序")
    content_type = Column(String(20), default="rich_text", nullable=False, comment="类型: rich_text/external_link")
    external_url = Column(String(500), nullable=True, comment="外部链接")
    rich_content = Column(Text, nullable=True, comment="富文本HTML")
    start_time = Column(DateTime, nullable=True, comment="模块开启时间")
    end_time = Column(DateTime, nullable=True, comment="模块关闭时间")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    site = relationship("Site", back_populates="modules")
    permissions = relationship("AccountModulePermission", back_populates="module", cascade="all, delete-orphan")
