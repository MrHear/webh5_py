"""
数据库模型定义
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, Text, Integer, DateTime, Enum, JSON, Boolean
from sqlalchemy.sql import func

from app.database import Base


class Post(Base):
    """文章模型"""
    __tablename__ = "posts"
    
    id = Column(String(36), primary_key=True, comment="文章UUID")
    title = Column(String(200), nullable=False, comment="文章标题")
    summary = Column(String(500), nullable=False, comment="文章摘要")
    content = Column(Text, nullable=False, comment="文章正文")
    type = Column(
        Enum("markdown", "richtext", name="post_type"),
        nullable=False,
        default="markdown",
        comment="文章类型"
    )
    tags = Column(JSON, comment="标签列表")
    views = Column(Integer, nullable=False, default=0, comment="阅读量")
    created_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )
    is_deleted = Column(Boolean, nullable=False, default=False, comment="软删除标记")
    
    def __repr__(self):
        return f"<Post(id={self.id}, title={self.title})>"
