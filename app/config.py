"""
应用配置模块
使用 pydantic-settings 进行类型安全的配置管理
"""
import os
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "onespace"
    
    # JWT配置
    # 默认密钥 (如果在 .env 中未配置)
    JWT_SECRET_KEY: str = "fallback-secret-key-please-change-in-production-random-string-2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    # 管理员配置
    ADMIN_USERNAME: str = "admin"
    # 默认密码: OneSpace_Secure_2026 (如果在 .env 中未配置)
    ADMIN_PASSWORD_HASH: str = "$2b$12$DVX/am4M4RP/tmcZYYWWKeTr0yqSz0.h6k7wki.98OohlfXmYMFBO"
    
    # 安全配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # 文件上传
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 运行模式
    DEBUG: bool = False
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def SYNC_DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


def get_settings() -> Settings:
    """获取配置实例（每次重新加载，支持热更新）"""
    return Settings()
