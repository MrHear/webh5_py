"""
认证路由模块
处理登录和Token管理
"""
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status, Request
from loguru import logger

from app.config import get_settings
from app.schemas import LoginRequest, LoginResponse, ApiResponse
from app.security import verify_password, create_access_token, get_client_ip
from app.rate_limiter import limiter

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=ApiResponse[LoginResponse])
@limiter.limit("5/minute")  # 登录接口严格限流
async def login(
    request: Request,
    login_data: LoginRequest
):
    """
    管理员登录
    
    - 验证用户名和密码
    - 返回JWT Token
    - 严格速率限制（每分钟5次）
    """
    client_ip = get_client_ip(request)
    
    # 验证用户名
    if login_data.username != settings.ADMIN_USERNAME:
        logger.warning(f"登录失败 - 用户名不存在: {login_data.username} from {client_ip}")
        # 使用统一的错误信息，防止用户名枚举
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证密码
    if not settings.ADMIN_PASSWORD_HASH:
        logger.error("管理员密码哈希未配置")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器配置错误"
        )
    
    if not verify_password(login_data.password, settings.ADMIN_PASSWORD_HASH):
        logger.warning(f"登录失败 - 密码错误: {login_data.username} from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成Token
    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": login_data.username},
        expires_delta=access_token_expires
    )
    
    logger.info(f"管理员登录成功: {login_data.username} from {client_ip}")
    
    return ApiResponse(
        code=200,
        message="登录成功",
        data=LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRE_MINUTES * 60
        )
    )
