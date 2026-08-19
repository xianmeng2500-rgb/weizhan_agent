"""微站模板 Schema"""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class SiteTemplateBase(BaseModel):
    name: str = Field(..., max_length=128, description="模板名称")
    description: Optional[str] = None
    template_key: str = Field("default", description="CSS风格: default/classic/dark/festive")
    layout: str = Field("grid", description="布局: grid/button/free")
    kv_image: Optional[str] = None
    title_config: Optional[dict[str, Any]] = None
    background_color: Optional[str] = None
    background_image: Optional[str] = None
    share_image: Optional[str] = None
    share_title: Optional[str] = Field(None, max_length=128)
    share_subtitle: Optional[str] = Field(None, max_length=255)
    preview_image: Optional[str] = None
    modules_config: Optional[list[dict[str, Any]]] = None
    status: str = Field("active", description="active/inactive")
    sort_order: int = 0


class SiteTemplateCreate(SiteTemplateBase):
    pass


class SiteTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    description: Optional[str] = None
    template_key: Optional[str] = None
    layout: Optional[str] = None
    kv_image: Optional[str] = None
    title_config: Optional[dict[str, Any]] = None
    background_color: Optional[str] = None
    background_image: Optional[str] = None
    share_image: Optional[str] = None
    share_title: Optional[str] = Field(None, max_length=128)
    share_subtitle: Optional[str] = Field(None, max_length=255)
    preview_image: Optional[str] = None
    modules_config: Optional[list[dict[str, Any]]] = None
    status: Optional[str] = None
    sort_order: Optional[int] = None


class SiteTemplateOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    template_key: str
    layout: str
    kv_image: Optional[str] = None
    title_config: Optional[dict[str, Any]] = None
    background_color: Optional[str] = None
    background_image: Optional[str] = None
    share_image: Optional[str] = None
    share_title: Optional[str] = None
    share_subtitle: Optional[str] = None
    preview_image: Optional[str] = None
    modules_config: Optional[list[dict[str, Any]]] = None
    is_system: bool
    status: str
    sort_order: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedSiteTemplates(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SiteTemplateOut]
