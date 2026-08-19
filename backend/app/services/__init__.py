"""阿里云OSS服务"""
import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, UploadFile
from app.config import settings
from app.database import SessionLocal
from app.models.system_config import SystemConfig


def get_storage_config() -> dict[str, str]:
    """获取存储配置：数据库系统配置优先，环境变量作为回退。"""
    db = SessionLocal()
    try:
        config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
        return {
            "access_key_id": (config.oss_access_key_id if config and config.oss_access_key_id else settings.OSS_ACCESS_KEY_ID),
            "access_key_secret": (config.oss_access_key_secret if config and config.oss_access_key_secret else settings.OSS_ACCESS_KEY_SECRET),
            "bucket_name": (config.oss_bucket_name if config and config.oss_bucket_name else settings.OSS_BUCKET_NAME),
            "endpoint": (config.oss_endpoint if config and config.oss_endpoint else settings.OSS_ENDPOINT),
            "custom_domain": (config.oss_custom_domain if config and config.oss_custom_domain else settings.OSS_CUSTOM_DOMAIN),
        }
    finally:
        db.close()


def oss_is_configured() -> bool:
    config = get_storage_config()
    return bool(config["access_key_id"] and config["access_key_secret"] and config["bucket_name"] and config["endpoint"])


def _get_oss_bucket(storage_config: dict[str, str]):
    """获取OSS Bucket实例(延迟初始化)"""
    import oss2

    auth = oss2.Auth(storage_config["access_key_id"], storage_config["access_key_secret"])
    return oss2.Bucket(auth, storage_config["endpoint"], storage_config["bucket_name"] )


async def upload_image(file: UploadFile) -> str:
    """上传图片到OSS

    Returns:
        图片的可访问URL
    """
    # 校验文件类型
    ext = os.path.splitext(file.filename or "")[1].lower().lstrip(".")
    if ext not in settings.allowed_file_types_list:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: .{ext}，仅支持 {', '.join(settings.allowed_file_types_list)}")

    # 读取文件内容
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制({settings.MAX_FILE_SIZE // 1024 // 1024}MB)")

    # 生成文件路径: weizhan/yyyy/mm/dd/uuid.ext
    now = datetime.now()
    file_key = f"weizhan/{now.strftime('%Y/%m/%d')}/{uuid.uuid4().hex}.{ext}"

    # 上传到OSS
    storage_config = get_storage_config()
    bucket = _get_oss_bucket(storage_config)
    bucket.put_object(file_key, content)

    # 返回URL
    if storage_config["custom_domain"]:
        domain = storage_config["custom_domain"].rstrip('/')
        if not domain.startswith('http://') and not domain.startswith('https://'):
            domain = f"https://{domain}"
        return f"{domain}/{file_key}"
    else:
        return f"https://{storage_config['bucket_name']}.{storage_config['endpoint']}/{file_key}"


async def upload_image_local(file: UploadFile, upload_dir: str = None) -> str:
    """本地文件上传(未配置OSS时的后备方案)

    Args:
        file: 上传的文件
        upload_dir: 本地存储目录
    Returns:
        文件相对路径(通过/static访问)
    """
    if upload_dir is None:
        upload_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            settings.UPLOAD_DIR,
        )
    ext = os.path.splitext(file.filename or "")[1].lower().lstrip(".")
    if ext not in settings.allowed_file_types_list:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: .{ext}")

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过限制")

    now = datetime.now()
    dir_path = os.path.join(upload_dir, now.strftime("%Y/%m/%d"))
    os.makedirs(dir_path, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(dir_path, filename)
    with open(file_path, "wb") as f:
        f.write(content)

    # 返回相对路径
    rel_path = os.path.relpath(file_path, upload_dir)
    return f"/static/uploads/{rel_path}"


def upload_image_bytes(content: bytes, ext: str = "png") -> str:
    """将字节内容直接落盘到 OSS（已配置时）或本地存储。

    供 AI 生成结果转存、参考图转存等非 UploadFile 场景复用。
    与 upload_image 保持一致的文件路径规则：weizhan/yyyy/mm/dd/uuid.ext

    Args:
        content: 图片字节内容
        ext: 文件扩展名（不含点，如 png/jpg）
    Returns:
        图片的可访问 URL
    """
    now = datetime.now()
    file_key = f"weizhan/{now.strftime('%Y/%m/%d')}/{uuid.uuid4().hex}.{ext}"

    if oss_is_configured():
        storage_config = get_storage_config()
        bucket = _get_oss_bucket(storage_config)
        bucket.put_object(file_key, content)
        if storage_config["custom_domain"]:
            domain = storage_config["custom_domain"].rstrip("/")
            if not domain.startswith("http://") and not domain.startswith("https://"):
                domain = f"https://{domain}"
            return f"{domain}/{file_key}"
        return f"https://{storage_config['bucket_name']}.{storage_config['endpoint']}/{file_key}"

    # 本地存储
    upload_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        settings.UPLOAD_DIR,
    )
    dir_path = os.path.join(upload_dir, now.strftime("%Y/%m/%d"))
    os.makedirs(dir_path, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(dir_path, filename)
    with open(file_path, "wb") as f:
        f.write(content)
    rel_path = os.path.relpath(file_path, upload_dir)
    return f"/static/uploads/{rel_path}"
