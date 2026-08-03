"""模块相关Schema"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ModuleBase(BaseModel):
    title: str = Field(..., max_length=128, description="模块标题")
    icon: Optional[str] = None
    sort_order: int = Field(0, ge=0, description="排序")
    content_type: str = Field("rich_text", description="rich_text/external_link")
    external_url: Optional[str] = None
    rich_content: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: bool = True


class ModuleCreate(ModuleBase):
    pass


class ModuleUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=128)
    icon: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    content_type: Optional[str] = None
    external_url: Optional[str] = None
    rich_content: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: Optional[bool] = None


class ModuleOut(BaseModel):
    id: int
    site_id: int
    title: str
    icon: Optional[str] = None
    sort_order: int
    content_type: str
    external_url: Optional[str] = None
    rich_content: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ModuleSortItem(BaseModel):
    module_id: int
    sort_order: int


class ModuleSortRequest(BaseModel):
    items: list[ModuleSortItem]
