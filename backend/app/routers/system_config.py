"""仅超级管理员可访问的系统配置接口"""
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SystemConfig, User
from app.schemas.system_config import SystemConfigOut, SystemConfigUpdate
from app.utils.deps import ROLE_SUPER_ADMIN, get_current_admin

router = APIRouter(prefix="/system-config", tags=["系统配置"])


def require_super_admin(current: User) -> None:
    if current.role != ROLE_SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅超级管理员可配置系统参数")


def get_config(db: Session) -> SystemConfig:
    config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
    if not config:
        config = SystemConfig(id=1)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def to_out(config: SystemConfig) -> SystemConfigOut:
    try:
        icons = json.loads(config.local_icon_library) if config.local_icon_library else []
        if not isinstance(icons, list):
            icons = []
    except (TypeError, json.JSONDecodeError):
        icons = []
    return SystemConfigOut(
        h5_domain=config.h5_domain or "",
        wechat_share_enabled=config.wechat_share_enabled,
        wechat_app_id=config.wechat_app_id or "",
        wechat_app_secret_configured=bool(config.wechat_app_secret),
        oss_access_key_id=config.oss_access_key_id or "",
        oss_access_key_secret_configured=bool(config.oss_access_key_secret),
        oss_bucket_name=config.oss_bucket_name or "",
        oss_endpoint=config.oss_endpoint or "",
        oss_custom_domain=config.oss_custom_domain or "",
        local_icon_library=icons,
        ai_provider=config.ai_provider or "dashscope",
        ai_api_key_configured=bool(config.ai_api_key),
        ai_image_model=config.ai_image_model or "wanx2.1-t2i-turbo",
    )


@router.get("/runtime")
def read_runtime_config(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """供后台编辑器读取的非敏感运行时配置。"""
    config = get_config(db)
    try:
        icons = json.loads(config.local_icon_library) if config.local_icon_library else []
        if not isinstance(icons, list):
            icons = []
    except (TypeError, json.JSONDecodeError):
        icons = []
    return {
        "h5_domain": (config.h5_domain or "").rstrip("/"),
        "local_icon_library": icons,
    }


@router.get("", response_model=SystemConfigOut)
def read_system_config(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    require_super_admin(current)
    return to_out(get_config(db))


@router.put("", response_model=SystemConfigOut)
def update_system_config(
    req: SystemConfigUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    require_super_admin(current)
    config = get_config(db)
    data = req.model_dump(exclude_unset=True)

    if "local_icon_library" in data:
        config.local_icon_library = json.dumps(data.pop("local_icon_library"), ensure_ascii=False)

    # 机密字段传空字符串时视为“不更新”；要清空请在数据库或环境变量中处理。
    for secret_field in ("wechat_app_secret", "oss_access_key_secret", "ai_api_key"):
        if secret_field in data and not data[secret_field]:
            data.pop(secret_field)

    for field, value in data.items():
        setattr(config, field, value)
    config.updated_by = current.id
    db.commit()
    db.refresh(config)
    return to_out(config)
