"""模块相关Schema"""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator


class ModuleBase(BaseModel):
    title: str = Field(..., max_length=128, description="模块标题")
    icon: Optional[str] = None
    sort_order: int = Field(0, ge=0, description="排序")
    content_type: str = Field("rich_text", description="rich_text/external_link/registration_form/schedule/qrcode")
    external_url: Optional[str] = None
    rich_content: Optional[str] = None
    form_config: Optional[dict] = Field(None, description="报名表单设计配置(JSON)")
    schedule_config: Optional[dict] = Field(None, description="日程安排配置(JSON)")
    qrcode_config: Optional[dict] = Field(None, description="我的二维码配置(JSON)")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: bool = True
    position_x: Optional[float] = Field(None, ge=0, le=100, description="自由布局X坐标(百分比)")
    position_y: Optional[float] = Field(None, ge=0, le=100, description="自由布局Y坐标(百分比)")
    width: Optional[float] = Field(None, ge=0, le=100, description="按钮宽度(百分比, null=自适应)")
    height: Optional[float] = Field(None, ge=0, le=100, description="按钮高度(百分比, null=自适应内容)")
    border_radius: Optional[int] = Field(None, ge=0, le=999, description="按钮圆角(px)")
    bg_color: Optional[str] = Field(None, max_length=50, description="按钮背景色(hex)")
    font_color: Optional[str] = Field(None, max_length=50, description="按钮文字颜色(hex)")
    icon_position: Optional[str] = Field(None, description="图标相对标题位置(left/right/top/bottom)")
    content_align: Optional[str] = Field(None, description="内容水平对齐(left/center/right)")
    show_arrow: Optional[bool] = Field(None, description="是否显示右侧箭头(null=默认显示)")

    @model_validator(mode="before")
    @classmethod
    def empty_str_to_none(cls, data: Any) -> Any:
        """将空字符串转为 None，解决前端空字符串无法被 Pydantic 解析为 Optional[datetime] 的问题"""
        if isinstance(data, dict):
            for field in ("start_time", "end_time"):
                if data.get(field) == "":
                    data[field] = None
        return data


class ModuleCreate(ModuleBase):
    pass


class ModuleUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=128)
    icon: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    content_type: Optional[str] = None
    external_url: Optional[str] = None
    rich_content: Optional[str] = None
    form_config: Optional[dict] = None
    schedule_config: Optional[dict] = None
    qrcode_config: Optional[dict] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: Optional[bool] = None
    position_x: Optional[float] = Field(None, ge=0, le=100)
    position_y: Optional[float] = Field(None, ge=0, le=100)
    width: Optional[float] = Field(None, ge=0, le=100)
    height: Optional[float] = Field(None, ge=0, le=100)
    border_radius: Optional[int] = Field(None, ge=0, le=999)
    bg_color: Optional[str] = Field(None, max_length=50)
    font_color: Optional[str] = Field(None, max_length=50)
    icon_position: Optional[str] = None
    content_align: Optional[str] = None
    show_arrow: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def empty_str_to_none(cls, data: Any) -> Any:
        """将空字符串转为 None，解决前端空字符串无法被 Pydantic 解析为 Optional[datetime] 的问题"""
        if isinstance(data, dict):
            for field in ("start_time", "end_time"):
                if data.get(field) == "":
                    data[field] = None
        return data


class ModuleOut(BaseModel):
    id: int
    site_id: int
    title: str
    icon: Optional[str] = None
    sort_order: int
    content_type: str
    external_url: Optional[str] = None
    rich_content: Optional[str] = None
    form_config: Optional[dict] = None
    schedule_config: Optional[dict] = None
    qrcode_config: Optional[dict] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: bool
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    border_radius: Optional[int] = None
    bg_color: Optional[str] = None
    font_color: Optional[str] = None
    icon_position: Optional[str] = None
    content_align: Optional[str] = None
    show_arrow: Optional[bool] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ModuleSortItem(BaseModel):
    module_id: int
    sort_order: int


class ModuleSortRequest(BaseModel):
    items: list[ModuleSortItem]


class ModulePositionItem(BaseModel):
    module_id: int
    position_x: Optional[float] = None
    position_y: Optional[float] = None


class ModulePositionRequest(BaseModel):
    items: list[ModulePositionItem]
