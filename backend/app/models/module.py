"""模块模型"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
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
    content_type = Column(String(20), default="rich_text", nullable=False, comment="类型: rich_text/external_link/registration_form/schedule/qrcode")
    external_url = Column(String(500), nullable=True, comment="外部链接")
    rich_content = Column(Text, nullable=True, comment="富文本HTML")
    form_config = Column(JSON, nullable=True, comment="报名表单设计配置(JSON)")
    schedule_config = Column(JSON, nullable=True, comment="日程安排配置(JSON)，格式: {items: [{date, time, topic, personnel}]}")
    qrcode_config = Column(JSON, nullable=True, comment="我的二维码配置(JSON)，格式: {hint, display_fields}")
    start_time = Column(DateTime, nullable=True, comment="模块开启时间")
    end_time = Column(DateTime, nullable=True, comment="模块关闭时间")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    position_x = Column(Float, nullable=True, comment="自由布局X坐标(百分比0-100)")
    position_y = Column(Float, nullable=True, comment="自由布局Y坐标(百分比0-100)")
    # 自由拖拽模式下的尺寸/形状样式（null 表示使用默认样式）
    width = Column(Float, nullable=True, comment="自由布局按钮宽度(百分比0-100，null=自适应)")
    height = Column(Float, nullable=True, comment="自由布局按钮高度(百分比0-100，null=自适应内容)")
    border_radius = Column(Integer, nullable=True, comment="按钮圆角(px，null=默认)")
    bg_color = Column(String(50), nullable=True, comment="按钮背景色(hex，null=模板默认)")
    font_color = Column(String(50), nullable=True, comment="按钮文字颜色(hex，null=模板默认)")
    icon_position = Column(String(10), nullable=True, comment="图标相对标题位置(left/right/top/bottom，null=left)")
    content_align = Column(String(10), nullable=True, comment="内容水平对齐(left/center/right，null=center)")
    show_arrow = Column(Boolean, nullable=True, comment="是否显示右侧箭头(null=默认显示)")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")

    # 关系
    site = relationship("Site", back_populates="modules")
    permissions = relationship("AccountModulePermission", back_populates="module", cascade="all, delete-orphan")
    form_submissions = relationship("FormSubmission", back_populates="module", cascade="all, delete-orphan")
    click_logs = relationship("ModuleClickLog", back_populates="module", cascade="all, delete-orphan")
