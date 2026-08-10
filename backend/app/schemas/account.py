"""账号相关Schema"""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class AccountImportItem(BaseModel):
    username: str = Field(..., max_length=64)
    password: Optional[str] = Field(None, description="明文密码，无密码模式下可省略")
    nickname: Optional[str] = None
    phone: Optional[str] = None
    custom_fields: Optional[dict[str, Any]] = None


class AccountImportRequest(BaseModel):
    accounts: list[AccountImportItem]


class AccountCreate(BaseModel):
    username: str = Field(..., max_length=64, description="登录账号")
    password: Optional[str] = Field(None, description="明文密码，无密码模式下可省略")
    nickname: Optional[str] = Field(None, max_length=64)
    phone: Optional[str] = Field(None, max_length=20)
    custom_fields: Optional[dict[str, Any]] = None


class AccountUpdate(BaseModel):
    username: Optional[str] = Field(None, max_length=64)
    password: Optional[str] = None
    nickname: Optional[str] = None
    phone: Optional[str] = None
    custom_fields: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class AccountOut(BaseModel):
    id: int
    site_id: int
    username: str
    nickname: Optional[str] = None
    phone: Optional[str] = None
    custom_fields: Optional[dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    permitted_module_ids: list[int] = []

    model_config = {"from_attributes": True}


class PaginatedAccounts(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AccountOut]


class AccountPermissionUpdate(BaseModel):
    module_ids: list[int]
