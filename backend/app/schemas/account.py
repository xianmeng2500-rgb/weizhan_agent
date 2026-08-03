"""账号相关Schema"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AccountImportItem(BaseModel):
    username: str = Field(..., max_length=64)
    password: str = Field(..., description="明文密码")
    nickname: Optional[str] = None
    phone: Optional[str] = None


class AccountImportRequest(BaseModel):
    accounts: list[AccountImportItem]


class AccountUpdate(BaseModel):
    password: Optional[str] = None
    nickname: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class AccountOut(BaseModel):
    id: int
    site_id: int
    username: str
    nickname: Optional[str] = None
    phone: Optional[str] = None
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
