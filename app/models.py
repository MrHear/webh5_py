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


class Comment(Base):
    """评论模型"""
    __tablename__ = "comments"
    
    id = Column(String(36), primary_key=True, comment="评论UUID")
    post_id = Column(String(36), nullable=False, index=True, comment="关联文章ID")
    content = Column(String(1000), nullable=False, comment="评论内容")
    author = Column(String(50), nullable=False, default="匿名访客", comment="评论者昵称")
    is_guest = Column(Boolean, nullable=False, default=True, comment="是否游客评论")
    reply_to_id = Column(String(36), nullable=True, index=True, comment="回复的评论ID")
    likes = Column(Integer, nullable=False, default=0, comment="点赞数")
    created_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        comment="创建时间"
    )
    is_deleted = Column(Boolean, nullable=False, default=False, comment="软删除标记")
    # 审核状态: pending-待审核, approved-通过, rejected-违规
    moderation_status = Column(
        Enum("pending", "approved", "rejected", name="moderation_status"),
        nullable=False,
        default="pending",
        index=True,
        comment="审核状态"
    )
    moderation_reason = Column(String(500), nullable=True, comment="审核原因(违规时填写)")
    
    def __repr__(self):
        return f"<Comment(id={self.id}, post_id={self.post_id})>"


class CommentLike(Base):
    """评论点赞记录模型"""
    __tablename__ = "comment_likes"
    
    id = Column(String(36), primary_key=True, comment="点赞记录UUID")
    comment_id = Column(String(36), nullable=False, index=True, comment="评论ID")
    client_ip = Column(String(45), nullable=False, comment="客户端IP")
    created_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        comment="点赞时间"
    )
    
    def __repr__(self):
        return f"<CommentLike(id={self.id}, comment_id={self.comment_id})>"
