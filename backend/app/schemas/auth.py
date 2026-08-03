"""认证相关Schema"""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    nickname: str | None = None


class FrontendLoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    id: int
    username: str
    nickname: str | None = None
    role: str

    model_config = {"from_attributes": True}
