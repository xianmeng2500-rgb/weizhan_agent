"""文件上传路由"""
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.models import User
from app.utils.deps import get_current_admin
from app.services import (
    oss_is_configured,
    upload_image, upload_image_local,
    upload_attachment, upload_attachment_local,
)

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


@router.post("/file")
async def upload_attachment(
    file: UploadFile = File(...),
    current: User = Depends(get_current_admin),
):
    """上传资料附件（资料附件表模块专用）- 走附件白名单（PDF/Office/图片）和 50MB 大小限制

    优先OSS，未配置则存本地。文件按 attachments/yyyy/mm/dd/uuid.ext 路径存储。
    文件大小由前端在保存模块配置时从 el-upload.file.size 记录，无需后端额外返回。
    """
    if oss_is_configured():
        url = await upload_attachment(file)
    else:
        url = await upload_attachment_local(file)
    return {"url": url, "original_name": file.filename}
