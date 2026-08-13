"""微站相关Schema"""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator
from app.schemas.module import ModuleOut


class SiteBase(BaseModel):
    name: str = Field(..., max_length=128, description="微站名称")
    code: str = Field(..., max_length=64, description="唯一码")
    template: str = Field("classic", description="模板")
    layout: str = Field("grid", description="布局: grid/button")
    kv_image: Optional[str] = None
    background_color: Optional[str] = None
    background_image: Optional[str] = None
    share_image: Optional[str] = None
    share_title: Optional[str] = Field(None, max_length=128)
    share_subtitle: Optional[str] = Field(None, max_length=255)
    customer_service_config: Optional[dict[str, Any]] = None
    login_fields_config: Optional[list[dict[str, Any]]] = None
    login_form_config: Optional[dict[str, Any]] = None
    grid_offset_y: Optional[float] = 0.0
    need_login: bool = False
    login_require_password: bool = True
    need_checkin: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    close_message: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def empty_str_to_none(cls, data: Any) -> Any:
        """将空字符串转为 None，解决前端空字符串无法被 Pydantic 解析为 Optional[datetime] 的问题"""
        if isinstance(data, dict):
            # 这些 datetime 字段的空字符串会导致 Pydantic 校验失败
            for field in ("start_time", "end_time"):
                if data.get(field) == "":
                    data[field] = None
        return data


class SiteCreate(SiteBase):
    pass


class SiteUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    code: Optional[str] = Field(None, max_length=64)
    template: Optional[str] = None
    layout: Optional[str] = None
    kv_image: Optional[str] = None
    background_color: Optional[str] = None
    background_image: Optional[str] = None
    share_image: Optional[str] = None
    share_title: Optional[str] = Field(None, max_length=128)
    share_subtitle: Optional[str] = Field(None, max_length=255)
    customer_service_config: Optional[dict[str, Any]] = None
    login_fields_config: Optional[list[dict[str, Any]]] = None
    login_form_config: Optional[dict[str, Any]] = None
    grid_offset_y: Optional[float] = None
    need_login: Optional[bool] = None
    login_require_password: Optional[bool] = None
    need_checkin: Optional[bool] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    close_message: Optional[str] = None


class SiteStatusUpdate(BaseModel):
    status: str = Field(..., description="draft/online/offline")


class SiteOut(BaseModel):
    id: int
    name: str
    code: str
    template: str
    layout: str
    kv_image: Optional[str] = None
    background_color: Optional[str] = None
    background_image: Optional[str] = None
    share_image: Optional[str] = None
    share_title: Optional[str] = None
    share_subtitle: Optional[str] = None
    customer_service_config: Optional[dict[str, Any]] = None
    login_fields_config: Optional[list[dict[str, Any]]] = None
    login_form_config: Optional[dict[str, Any]] = None
    grid_offset_y: Optional[float] = None
    need_login: bool
    login_require_password: bool = True
    need_checkin: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str
    close_message: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    module_count: int = 0
    account_count: int = 0

    model_config = {"from_attributes": True}


class SiteOutWithModules(SiteOut):
    modules: list[ModuleOut] = []


class PaginatedSites(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SiteOut]
