"""
Pydantic 数据模式定义
用于请求验证和响应序列化
"""
from datetime import datetime
from typing import List, Optional, Generic, TypeVar
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict
import bleach


class PostType(str, Enum):
    """文章类型枚举"""
    markdown = "markdown"
    richtext = "richtext"


# ============== 文章相关模式 ==============

class PostBase(BaseModel):
    """文章基础字段"""
    title: str = Field(..., min_length=1, max_length=200, description="文章标题")
    summary: str = Field(..., min_length=1, max_length=500, description="文章摘要")
    type: PostType = Field(default=PostType.markdown, description="文章类型")
    tags: Optional[List[str]] = Field(default=[], description="标签列表")
    
    @field_validator("title", "summary")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        """清理文本，防止XSS攻击"""
        # 移除所有HTML标签，只保留纯文本
        return bleach.clean(v.strip(), tags=[], strip=True)
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> List[str]:
        """验证并清理标签"""
        if v is None:
            return []
        # 限制标签数量和长度
        cleaned = []
        for tag in v[:10]:  # 最多10个标签
            tag = bleach.clean(tag.strip(), tags=[], strip=True)[:50]  # 每个标签最多50字符
            if tag:
                cleaned.append(tag)
        return cleaned


class PostCreate(PostBase):
    """创建文章请求"""
    content: str = Field(..., min_length=1, max_length=500000, description="文章正文")
    
    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        """清理内容，允许安全的HTML标签"""
        # 允许的HTML标签（用于富文本）
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 's', 'blockquote',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li',
            'a', 'img',
            'pre', 'code',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'div', 'span'
        ]
        allowed_attrs = {
            '*': ['class', 'id'],
            'a': ['href', 'title', 'target', 'rel'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
        }
        return bleach.clean(
            v.strip(),
            tags=allowed_tags,
            attributes=allowed_attrs,
            strip=True
        )


class PostUpdate(BaseModel):
    """更新文章请求（部分更新）"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    summary: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1, max_length=500000)
    type: Optional[PostType] = None
    tags: Optional[List[str]] = None
    
    @field_validator("title", "summary")
    @classmethod
    def sanitize_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return bleach.clean(v.strip(), tags=[], strip=True)
    
    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 's', 'blockquote',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'a', 'img', 'pre', 'code',
            'table', 'thead', 'tbody', 'tr', 'th', 'td', 'div', 'span'
        ]
        allowed_attrs = {
            '*': ['class', 'id'],
            'a': ['href', 'title', 'target', 'rel'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
        }
        return bleach.clean(v.strip(), tags=allowed_tags, attributes=allowed_attrs, strip=True)


class PostInList(BaseModel):
    """列表中的文章（不含content）"""
    id: str
    title: str
    summary: str
    type: PostType
    tags: List[str] = []
    views: int
    createdAt: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PostDetail(PostInList):
    """文章详情（含content）"""
    content: str


# ============== 通用响应模式 ==============

DataT = TypeVar("DataT")


class ApiResponse(BaseModel, Generic[DataT]):
    """统一API响应格式"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="响应消息")
    data: Optional[DataT] = Field(None, description="响应数据")


class PaginatedData(BaseModel, Generic[DataT]):
    """分页数据"""
    total: int
    page: int
    list: List[DataT]


class PostCreateResponse(BaseModel):
    """创建文章响应数据"""
    id: str
    createdAt: datetime


# ============== 认证相关模式 ==============

class TokenData(BaseModel):
    """JWT Token数据"""
    username: Optional[str] = None
    exp: Optional[datetime] = None


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)
    
    @field_validator("username", "password")
    @classmethod
    def sanitize(cls, v: str) -> str:
        return v.strip()


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
