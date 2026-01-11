"""
安全模块
包含JWT认证、密码哈希、速率限制等安全功能
"""
import re
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from loguru import logger

from app.config import get_settings
from app.schemas import TokenData

settings = get_settings()

# HTTP Bearer认证
security = HTTPBearer(auto_error=False)


# ============== 密码处理 ==============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


# ============== JWT Token处理 ==============

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """解码JWT令牌"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        exp = payload.get("exp")
        if username is None:
            return None
        return TokenData(username=username, exp=datetime.fromtimestamp(exp, tz=timezone.utc))
    except JWTError as e:
        logger.warning(f"JWT解码失败: {e}")
        return None


# ============== 认证依赖 ==============

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """获取当前用户（可选认证）"""
    if credentials is None:
        return None
    
    token_data = decode_token(credentials.credentials)
    if token_data is None:
        return None
    
    return token_data.username


async def require_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """要求管理员权限"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if credentials is None:
        raise credentials_exception
    
    token_data = decode_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception
    
    if token_data.username != settings.ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    return token_data.username


# ============== 输入验证与安全检查 ==============

# SQL注入检测模式
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\b)",
    r"(--|\#|\/\*)",
    r"(\b(UNION|JOIN)\b.*\b(SELECT)\b)",
    r"(;.*\b(SELECT|INSERT|UPDATE|DELETE)\b)",
]


def detect_sql_injection(value: str) -> bool:
    """检测SQL注入尝试"""
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    return False


# XSS攻击检测模式
XSS_PATTERNS = [
    r"<script\b[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe\b",
    r"<object\b",
    r"<embed\b",
]


def detect_xss(value: str) -> bool:
    """检测XSS攻击尝试"""
    for pattern in XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    return False


# ============== 请求安全检查 ==============

def get_client_ip(request: Request) -> str:
    """获取客户端真实IP（考虑代理）"""
    # 优先从X-Forwarded-For获取
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # 取第一个IP（最原始的客户端IP）
        return forwarded.split(",")[0].strip()
    
    # 其次从X-Real-IP获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # 最后使用直连IP
    if request.client:
        return request.client.host
    
    return "unknown"


def generate_request_id(request: Request) -> str:
    """生成请求唯一标识"""
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    timestamp = datetime.now().isoformat()
    
    raw = f"{client_ip}-{user_agent}-{timestamp}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ============== 敏感信息过滤 ==============

def mask_sensitive_data(data: dict, sensitive_keys: list = None) -> dict:
    """掩盖敏感数据"""
    if sensitive_keys is None:
        sensitive_keys = ["password", "token", "secret", "api_key", "authorization"]
    
    masked = data.copy()
    for key in sensitive_keys:
        if key in masked:
            masked[key] = "***MASKED***"
    return masked
