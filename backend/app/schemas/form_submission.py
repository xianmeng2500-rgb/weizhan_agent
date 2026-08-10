"""表单提交记录相关Schema"""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class FormFieldConfig(BaseModel):
    """表单字段配置项（仅用于文档说明）"""
    id: str
    type: str
    title: str
    required: bool = False
    placeholder: Optional[str] = None
    options: list[str] = []
    defaultValue: Any = None
    props: dict = {}


class FormConfig(BaseModel):
    """报名表单完整配置（仅用于文档说明）"""
    title: str = "活动报名表"
    description: str = ""
    buttonText: str = "提交"
    fields: list[FormFieldConfig] = []


class FormSubmissionCreate(BaseModel):
    """公开提交报名表单"""
    data: dict[str, Any] = Field(..., description="字段ID到值的映射")
    submitter_name: Optional[str] = Field(None, max_length=128)
    submitter_phone: Optional[str] = Field(None, max_length=20)


class FormSubmissionUpdate(BaseModel):
    """管理员更新提交记录备注"""
    note: Optional[str] = None


class FormSubmissionOut(BaseModel):
    id: int
    site_id: int
    module_id: int
    account_id: Optional[int] = None
    submitter_name: Optional[str] = None
    submitter_phone: Optional[str] = None
    data: dict[str, Any]
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
