"""认证相关Schema"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    nickname: str | None = None
    role: str | None = None


class FrontendLoginRequest(BaseModel):
    username: str
    password: str | None = None  # 无密码模式下可不传
    login_field: str | None = None  # 使用哪个登录字段标识 (如 "username", "phone", "custom_xxx")
    custom_fields: dict[str, str] | None = None  # 自定义字段值
    login_fields: dict[str, str] | None = None  # 所有配置的登录字段值 {key: value}，用于多字段匹配


class UserInfo(BaseModel):
    id: int
    username: str
    nickname: str | None = None
    role: str
    is_active: bool = True

    model_config = {"from_attributes": True}


class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=6, max_length=64)
    nickname: Optional[str] = Field(None, max_length=64)
    role: str = Field("sub_admin", description="角色: super_admin/admin/sub_admin")


class AdminUserUpdate(BaseModel):
    password: Optional[str] = Field(None, min_length=6, max_length=64)
    nickname: Optional[str] = Field(None, max_length=64)
    role: Optional[str] = None
    is_active: Optional[bool] = None


class AdminUserOut(BaseModel):
    id: int
    username: str
    nickname: Optional[str] = None
    role: str
    is_active: bool
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
