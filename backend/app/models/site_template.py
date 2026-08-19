"""微站模板模型"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from app.database import Base


class SiteTemplate(Base):
    """微站模板 - 管理员可预设外观配置和模块结构，用户创建微站时可直接套用"""
    __tablename__ = "site_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, comment="模板名称")
    description = Column(Text, nullable=True, comment="模板描述")
    # 外观配置（套用时复制到 site 对应字段）
    template_key = Column(String(20), default="default", nullable=False, comment="CSS风格: default/classic/dark/festive")
    layout = Column(String(20), default="grid", nullable=False, comment="布局: grid/button/free")
    kv_image = Column(String(500), nullable=True, comment="KV图URL")
    title_config = Column(Text, nullable=True, comment="微站标题装饰配置JSON")
    background_color = Column(String(20), nullable=True, comment="背景色")
    background_image = Column(String(500), nullable=True, comment="背景图URL")
    # 分享配置
    share_image = Column(String(500), nullable=True, comment="微信分享图标")
    share_title = Column(String(128), nullable=True, comment="微信分享标题")
    share_subtitle = Column(String(255), nullable=True, comment="微信分享副标题")
    # 预览图（用于模板选择界面展示）
    preview_image = Column(String(500), nullable=True, comment="模板预览图URL")
    # 预置模块配置 (JSON数组，套用时自动创建对应模块)
    modules_config = Column(Text, nullable=True, comment="预置模块配置JSON")
    # 状态与管理
    is_system = Column(Boolean, default=False, nullable=False, comment="系统内置模板不可删除")
    status = Column(String(20), default="active", nullable=False, comment="状态: active/inactive")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序(越小越靠前)")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建者")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")
