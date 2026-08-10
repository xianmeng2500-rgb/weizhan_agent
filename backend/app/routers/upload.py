"""文件上传路由"""
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.models import User
from app.utils.deps import get_current_admin
from app.services import oss_is_configured, upload_image, upload_image_local

router = APIRouter(prefix="/upload", tags=["文件上传"])


@router.post("/image")
async def upload_file(
    file: UploadFile = File(...),
    current: User = Depends(get_current_admin),
):
    """上传图片 - 优先OSS，未配置则存本地"""
    # 检查OSS是否配置
    if oss_is_configured():
        url = await upload_image(file)
    else:
        url = await upload_image_local(file)
    return {"url": url, "original_name": file.filename}
