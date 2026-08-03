"""阿里云OSS服务"""
import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, UploadFile
from app.config import settings


def _get_oss_bucket():
    """获取OSS Bucket实例(延迟初始化)"""
    import oss2

    auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
    return oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)


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
    bucket = _get_oss_bucket()
    bucket.put_object(file_key, content)

    # 返回URL
    if settings.OSS_CUSTOM_DOMAIN:
        domain = settings.OSS_CUSTOM_DOMAIN.rstrip('/')
        if not domain.startswith('http://') and not domain.startswith('https://'):
            domain = f"https://{domain}"
        return f"{domain}/{file_key}"
    else:
        return f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{file_key}"


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
