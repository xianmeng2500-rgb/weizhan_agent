"""系统级配置模型（单例）"""
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from app.database import Base


class SystemConfig(Base):
    """系统级配置。仅保留 id=1 的单例记录。"""
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, default=1)
    h5_domain = Column(String(500), nullable=True, comment="移动端 H5 对外域名")

    wechat_share_enabled = Column(Boolean, default=False, nullable=False, comment="是否启用微信分享")
    wechat_app_id = Column(String(128), nullable=True, comment="微信 AppID")
    wechat_app_secret = Column(String(255), nullable=True, comment="微信 AppSecret")

    oss_access_key_id = Column(String(255), nullable=True, comment="OSS AccessKey ID")
    oss_access_key_secret = Column(String(255), nullable=True, comment="OSS AccessKey Secret")
    oss_bucket_name = Column(String(255), nullable=True, comment="OSS Bucket")
    oss_endpoint = Column(String(500), nullable=True, comment="OSS Endpoint")
    oss_custom_domain = Column(String(500), nullable=True, comment="OSS 自定义域名")

    local_icon_library = Column(Text, nullable=True, comment="本地图标库 JSON")
    ai_provider = Column(String(50), default="dashscope", nullable=False, comment="AI 服务商")
    ai_api_key = Column(String(255), nullable=True, comment="AI API Key（通义万相/DashScope）")
    ai_image_model = Column(String(100), default="wanx2.1-t2i-turbo", nullable=False, comment="AI 生图模型")
    updated_by = Column(Integer, nullable=True, comment="最后修改人")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
