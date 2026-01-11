"""
速率限制模块
防止API滥用和DDoS攻击
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.security import get_client_ip

settings = get_settings()


def get_real_client_ip(request: Request) -> str:
    """获取真实客户端IP（考虑反向代理）"""
    return get_client_ip(request)


# 创建限流器实例
limiter = Limiter(
    key_func=get_real_client_ip,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri="memory://",  # 使用内存存储，生产环境建议使用Redis
    # storage_uri=settings.REDIS_URL,  # 生产环境使用Redis
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """速率限制超出处理器"""
    return JSONResponse(
        status_code=429,
        content={
            "code": 429,
            "message": "请求过于频繁，请稍后再试",
            "detail": str(exc.detail) if hasattr(exc, 'detail') else "Rate limit exceeded"
        }
    )


def setup_rate_limiter(app: FastAPI) -> None:
    """设置速率限制"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
