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
    """管理员更新提交记录（备注 / 单条数据级修改权限）"""
    note: Optional[str] = None
    allow_edit: Optional[bool] = Field(None, description="是否允许提交后修改（单条数据级，需模块级允许才生效）")


class FormSubmissionSelfUpdate(BaseModel):
    """H5 用户修改自己已提交的报名数据"""
    data: dict[str, Any] = Field(..., description="字段ID到值的映射")
    submitter_name: Optional[str] = Field(None, max_length=128)
    submitter_phone: Optional[str] = Field(None, max_length=20)


class FormSubmissionOut(BaseModel):
    id: int
    site_id: int
    module_id: int
    account_id: Optional[int] = None
    submitter_name: Optional[str] = None
    submitter_phone: Optional[str] = None
    data: dict[str, Any]
    note: Optional[str] = None
    allow_edit: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}
