"""应用配置管理"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置 - 从环境变量读取"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # 应用配置
    APP_NAME: str = "微站系统"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-in-production"
    API_V1_PREFIX: str = "/api/v1"

    # 数据库配置
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "weizhan"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # 超级管理员初始账号（首次启动自动创建，可在 .env 中修改）
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"

    # JWT配置
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 后台: 24小时
    JWT_FRONTEND_EXPIRE_MINUTES: int = 720  # 前端微站: 12小时

    # 阿里云OSS配置
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_BUCKET_NAME: str = ""
    OSS_ENDPOINT: str = "oss-cn-hangzhou.aliyuncs.com"
    OSS_CUSTOM_DOMAIN: str = ""

    # 上传配置
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_FILE_TYPES: str = "jpg,png,gif,webp,jpeg"
    UPLOAD_DIR: str = "uploads"

    # CORS配置
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174"

    # AI 生图配置（环境变量回退；优先从 SystemConfig 表读取）
    DASHSCOPE_API_KEY: str = ""
    AI_PROVIDER: str = "dashscope"
    AI_IMAGE_MODEL: str = "wan2.2-t2i-flash"

    # IP 限流配置（防接口攻击/刷库）
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_WINDOW: int = 60  # 限流窗口(秒)
    RATE_LIMIT_LOGIN_MAX: int = 10  # 登录接口/每IP/窗口: 防暴力破解与 bcrypt CPU DoS
    RATE_LIMIT_WRITE_MAX: int = 120  # 公开写库接口(access/click/表单提交)/每IP/窗口
    RATE_LIMIT_EXTERNAL_MAX: int = 20  # 外部API调用(微信签名/AI生图)/每IP/窗口
    RATE_LIMIT_DEFAULT_MAX: int = 300  # 其他接口/每IP/窗口: 通用兜底

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_file_types_list(self) -> List[str]:
        return [t.strip().lower() for t in self.ALLOWED_FILE_TYPES.split(",") if t.strip()]

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )


settings = Settings()
