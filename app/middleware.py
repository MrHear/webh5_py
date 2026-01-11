"""
中间件模块
包含请求日志、安全检查、CORS等中间件
"""
import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from app.config import get_settings
from app.security import get_client_ip, detect_sql_injection, detect_xss

settings = get_settings()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        start_time = time.time()
        
        # 将请求ID添加到request state
        request.state.request_id = request_id
        request.state.client_ip = client_ip
        
        # 记录请求
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"- Client: {client_ip}"
        )
        
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = (time.time() - start_time) * 1000
            
            # 记录响应
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Time: {process_time:.2f}ms"
            )
            
            # 添加安全响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            return response
            
        except Exception as e:
            logger.error(f"[{request_id}] 请求处理异常: {str(e)}")
            raise


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全检查中间件"""
    
    # 可疑User-Agent列表
    BLOCKED_USER_AGENTS = [
        "sqlmap",
        "nikto",
        "nmap",
        "masscan",
        "zgrab",
        "python-requests",  # 可根据需要移除
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "").lower()
        
        # 检查User-Agent (可选，根据实际需求调整)
        # for blocked in self.BLOCKED_USER_AGENTS:
        #     if blocked.lower() in user_agent:
        #         logger.warning(f"阻止可疑User-Agent: {user_agent} from {client_ip}")
        #         return Response(
        #             content='{"code": 403, "message": "Access Denied"}',
        #             status_code=403,
        #             media_type="application/json"
        #         )
        
        # 检查查询参数中的SQL注入
        for key, value in request.query_params.items():
            if detect_sql_injection(value):
                logger.warning(f"检测到SQL注入尝试: {key}={value} from {client_ip}")
                return Response(
                    content='{"code": 400, "message": "Invalid request parameters"}',
                    status_code=400,
                    media_type="application/json"
                )
        
        # 检查路径中的攻击模式
        path = request.url.path
        suspicious_patterns = [
            "../", "..\\",  # 路径遍历
            ".php", ".asp", ".jsp",  # 非法扩展名探测
            "/wp-", "/wordpress",  # WordPress扫描
            "/admin.php", "/phpmyadmin",  # 管理后台扫描
        ]
        
        for pattern in suspicious_patterns:
            if pattern in path.lower():
                logger.warning(f"检测到可疑路径访问: {path} from {client_ip}")
                return Response(
                    content='{"code": 404, "message": "Not Found"}',
                    status_code=404,
                    media_type="application/json"
                )
        
        return await call_next(request)


def setup_middlewares(app: FastAPI) -> None:
    """设置所有中间件"""
    
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    
    # 安全检查中间件
    app.add_middleware(SecurityMiddleware)
    
    # 请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)
