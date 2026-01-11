"""
文件上传路由模块
安全处理图片上传
"""
import os
import uuid
import hashlib
import mimetypes
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from loguru import logger

from app.config import get_settings
from app.schemas import ApiResponse
from app.security import require_admin
from app.rate_limiter import limiter
from app.utils import now_beijing

settings = get_settings()
router = APIRouter(prefix="/upload", tags=["文件上传"])

# 允许的图片MIME类型
ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}

# 文件头魔数检测
FILE_SIGNATURES = {
    b'\xff\xd8\xff': "image/jpeg",
    b'\x89PNG\r\n\x1a\n': "image/png",
    b'GIF87a': "image/gif",
    b'GIF89a': "image/gif",
    b'RIFF': "image/webp",  # WebP (需要进一步验证)
}


def validate_file_signature(content: bytes) -> str | None:
    """通过文件头魔数验证文件类型"""
    for signature, mime_type in FILE_SIGNATURES.items():
        if content.startswith(signature):
            return mime_type
    
    # WebP额外检查
    if content[:4] == b'RIFF' and content[8:12] == b'WEBP':
        return "image/webp"
    
    return None


class UploadResponse(ApiResponse):
    """上传响应"""
    pass


@router.post("", response_model=ApiResponse)
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="要上传的图片文件"),
    admin: str = Depends(require_admin)
):
    """
    上传图片
    
    - 需要管理员权限
    - 仅支持 JPEG、PNG、GIF、WebP 格式
    - 文件大小限制由配置决定
    - 使用文件内容哈希作为文件名，防止重复上传
    """
    # 检查文件是否存在
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未选择文件"
        )
    
    # 读取文件内容
    content = await file.read()
    
    # 检查文件大小
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件大小超过限制（最大 {settings.MAX_UPLOAD_SIZE_MB}MB）"
        )
    
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件内容为空"
        )
    
    # 验证MIME类型（通过文件头魔数）
    detected_mime = validate_file_signature(content)
    if not detected_mime or detected_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="不支持的文件类型，仅支持 JPEG、PNG、GIF、WebP"
        )
    
    # 获取正确的扩展名
    extension = ALLOWED_MIME_TYPES[detected_mime]
    
    # 使用内容哈希作为文件名（去重）
    content_hash = hashlib.sha256(content).hexdigest()[:16]
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{content_hash}-{unique_id}{extension}"
    
    # 确保上传目录存在
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # 按日期组织文件（使用北京时间）
    date_dir = now_beijing().strftime("%Y/%m")
    file_dir = upload_dir / date_dir
    file_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存文件
    file_path = file_dir / filename
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # 生成访问URL
    relative_path = f"/uploads/{date_dir}/{filename}"
    
    logger.info(f"管理员 {admin} 上传了文件: {relative_path}")
    
    return ApiResponse(
        code=200,
        message="上传成功",
        data={
            "url": relative_path,
            "filename": filename,
            "size": len(content),
            "mime_type": detected_mime
        }
    )
