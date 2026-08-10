"""系统配置 Schema"""
import json
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class SystemConfigUpdate(BaseModel):
    h5_domain: Optional[str] = Field(None, max_length=500)
    wechat_share_enabled: Optional[bool] = None
    wechat_app_id: Optional[str] = Field(None, max_length=128)
    wechat_app_secret: Optional[str] = Field(None, max_length=255)
    oss_access_key_id: Optional[str] = Field(None, max_length=255)
    oss_access_key_secret: Optional[str] = Field(None, max_length=255)
    oss_bucket_name: Optional[str] = Field(None, max_length=255)
    oss_endpoint: Optional[str] = Field(None, max_length=500)
    oss_custom_domain: Optional[str] = Field(None, max_length=500)
    local_icon_library: Optional[list[dict[str, Any]]] = None

    @field_validator("h5_domain", "oss_custom_domain")
    @classmethod
    def normalize_domain(cls, value: Optional[str]) -> Optional[str]:
        return value.strip().rstrip("/") if value else value


class SystemConfigOut(BaseModel):
    h5_domain: str = ""
    wechat_share_enabled: bool = False
    wechat_app_id: str = ""
    wechat_app_secret_configured: bool = False
    oss_access_key_id: str = ""
    oss_access_key_secret_configured: bool = False
    oss_bucket_name: str = ""
    oss_endpoint: str = ""
    oss_custom_domain: str = ""
    local_icon_library: list[dict[str, Any]] = []
