"""微站相关Schema"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.module import ModuleOut


class SiteBase(BaseModel):
    name: str = Field(..., max_length=128, description="微站名称")
    code: str = Field(..., max_length=64, description="唯一码")
    template: str = Field("classic", description="模板")
    layout: str = Field("grid", description="布局: grid/button")
    kv_image: Optional[str] = None
    background_color: Optional[str] = None
    need_login: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    close_message: Optional[str] = None


class SiteCreate(SiteBase):
    pass


class SiteUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    code: Optional[str] = Field(None, max_length=64)
    template: Optional[str] = None
    layout: Optional[str] = None
    kv_image: Optional[str] = None
    background_color: Optional[str] = None
    need_login: Optional[bool] = None
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
    need_login: bool
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
