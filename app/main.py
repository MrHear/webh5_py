"""
OneSpace 博客系统 - 主应用入口
安全可靠的个人博客后端API
"""
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.config import get_settings
from app.middleware import setup_middlewares
from app.rate_limiter import setup_rate_limiter
from app.routes import posts, auth, upload, comments

# 配置日志
settings = get_settings()

# 移除默认的日志处理器
logger.remove()

# 添加控制台日志
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG" if settings.DEBUG else "INFO",
    colorize=True
)

# 添加文件日志（按天轮转）
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logger.add(
    log_dir / "app_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO",
    rotation="00:00",  # 每天午夜轮转
    retention="30 days",  # 保留30天
    compression="gz",  # 压缩旧日志
    encoding="utf-8"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("=" * 50)
    logger.info("OneSpace 博客系统启动中...")
    logger.info(f"运行模式: {'开发' if settings.DEBUG else '生产'}")
    logger.info("=" * 50)
    
    # 确保上传目录存在
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    yield
    
    logger.info("OneSpace 博客系统已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="OneSpace 博客系统 API",
    description="安全可靠的个人博客后端API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,  # 生产环境禁用Swagger
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# 设置中间件
setup_middlewares(app)

# 设置速率限制
setup_rate_limiter(app)

# 挂载静态文件目录（用于上传的图片）
upload_dir = Path(settings.UPLOAD_DIR)
if upload_dir.exists():
    app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")


# ============== 全局异常处理 ==============

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.exception(f"[{request_id}] 未处理的异常: {exc}")
    
    # 生产环境不暴露具体错误信息
    detail = str(exc) if settings.DEBUG else "服务器内部错误"
    
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": detail,
            "request_id": request_id
        }
    )


# ============== 注册路由 ==============

app.include_router(posts.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")
app.include_router(comments.router, prefix="/api/v1")


# ============== 健康检查 ==============

@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {
        "code": 200,
        "message": "ok",
        "data": {
            "status": "healthy",
            "version": "1.0.0"
        }
    }


@app.get("/", tags=["系统"])
async def root():
    """根路径"""
    return {
        "code": 200,
        "message": "OneSpace Blog API",
        "data": {
            "version": "1.0.0",
            "docs": "/docs" if settings.DEBUG else "API文档已禁用"
        }
    }
