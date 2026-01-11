"""
评论路由模块1
处理所有评论相关的API请求
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import select, func, update, or_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_db
from app.models import Comment, CommentLike, Post
from app.schemas import (
    CommentCreate, CommentInList, CommentCreateResponse,
    LikeResponse, ApiResponse, ReplyTo
)
from app.security import get_client_ip
from app.rate_limiter import limiter
from app.moderation import trigger_moderation

router = APIRouter(prefix="/comments", tags=["评论"])


@router.get("", response_model=ApiResponse[list[CommentInList]])
@limiter.limit("60/minute")
async def get_comments(
    request: Request,
    postId: str = Query(..., description="文章ID"),
    sort: str = Query("time", description="排序方式: time | likes"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取文章评论列表
    
    - 支持按时间或点赞数排序
    - 返回评论及其被回复的评论信息
    """
    # 验证UUID格式
    try:
        uuid.UUID(postId)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的文章ID格式"
        )
    
    # 验证文章是否存在
    post_query = select(Post).where(Post.id == postId, Post.is_deleted == False)
    post_result = await db.execute(post_query)
    if not post_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在"
        )
    
    # 查询评论 (排除被拒绝的评论)
    base_query = select(Comment).where(
        Comment.post_id == postId,
        Comment.is_deleted == False,
        Comment.moderation_status != "rejected"  # 过滤违规评论
    )
    
    # 排序
    if sort == "likes":
        base_query = base_query.order_by(Comment.likes.desc(), Comment.created_at.desc())
    else:
        base_query = base_query.order_by(Comment.created_at.desc())
    
    result = await db.execute(base_query)
    comments = result.scalars().all()
    
    # 获取当前客户端IP，用于判断是否点赞
    client_ip = get_client_ip(request)
    
    # 获取所有评论ID
    comment_ids = [c.id for c in comments]
    
    # 查询当前用户点赞的评论
    liked_comment_ids = set()
    if comment_ids:
        like_query = select(CommentLike.comment_id).where(
            CommentLike.comment_id.in_(comment_ids),
            CommentLike.client_ip == client_ip
        )
        like_result = await db.execute(like_query)
        liked_comment_ids = set(row[0] for row in like_result.fetchall())
    
    # 获取被回复的评论信息
    reply_to_ids = [c.reply_to_id for c in comments if c.reply_to_id]
    reply_to_map = {}
    if reply_to_ids:
        reply_query = select(Comment).where(Comment.id.in_(reply_to_ids))
        reply_result = await db.execute(reply_query)
        for reply_comment in reply_result.scalars().all():
            reply_to_map[reply_comment.id] = ReplyTo(
                id=reply_comment.id,
                author=reply_comment.author,
                content=reply_comment.content[:100] + "..." if len(reply_comment.content) > 100 else reply_comment.content
            )
    
    # 转换为响应格式
    comment_list = []
    for comment in comments:
        comment_list.append(CommentInList(
            id=comment.id,
            postId=comment.post_id,
            content=comment.content,
            author=comment.author,
            createdAt=comment.created_at,
            isGuest=comment.is_guest,
            likes=comment.likes,
            isLiked=comment.id in liked_comment_ids,
            replyTo=reply_to_map.get(comment.reply_to_id) if comment.reply_to_id else None
        ))
    
    return ApiResponse(
        code=200,
        message="success",
        data=comment_list
    )


@router.post("", response_model=ApiResponse[CommentCreateResponse], status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_comment(
    request: Request,
    comment_data: CommentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    发表评论
    
    - 游客可以评论
    - 支持回复其他评论
    - 自动生成UUID
    """
    # 验证文章ID格式
    try:
        uuid.UUID(comment_data.postId)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的文章ID格式"
        )
    
    # 验证文章是否存在
    post_query = select(Post).where(Post.id == comment_data.postId, Post.is_deleted == False)
    post_result = await db.execute(post_query)
    if not post_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在"
        )
    
    # 如果有回复ID，验证被回复的评论是否存在
    reply_to_comment = None
    if comment_data.replyToId:
        try:
            uuid.UUID(comment_data.replyToId)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的回复评论ID格式"
            )
        
        reply_query = select(Comment).where(
            Comment.id == comment_data.replyToId,
            Comment.post_id == comment_data.postId,
            Comment.is_deleted == False
        )
        reply_result = await db.execute(reply_query)
        reply_to_comment = reply_result.scalar_one_or_none()
        if not reply_to_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="被回复的评论不存在"
            )
    
    # 生成评论UUID
    comment_id = str(uuid.uuid4())
    
    # 设置作者名称
    author = comment_data.author if comment_data.author else "匿名访客"
    
    # 创建评论
    new_comment = Comment(
        id=comment_id,
        post_id=comment_data.postId,
        content=comment_data.content,
        author=author,
        is_guest=True,
        reply_to_id=comment_data.replyToId,
        likes=0,
        created_at=datetime.now()
    )
    
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    
    client_ip = get_client_ip(request)
    logger.info(f"新评论发表: {comment_id} on post {comment_data.postId} from {client_ip}")
    
    # 异步触发内容审核
    trigger_moderation(comment_id, comment_data.content)
    
    # 构建回复信息
    reply_to = None
    if reply_to_comment:
        reply_to = ReplyTo(
            id=reply_to_comment.id,
            author=reply_to_comment.author,
            content=reply_to_comment.content[:100] + "..." if len(reply_to_comment.content) > 100 else reply_to_comment.content
        )
    
    return ApiResponse(
        code=201,
        message="评论发表成功",
        data=CommentCreateResponse(
            id=comment_id,
            postId=new_comment.post_id,
            content=new_comment.content,
            author=new_comment.author,
            createdAt=new_comment.created_at,
            isGuest=new_comment.is_guest,
            likes=new_comment.likes,
            isLiked=False,
            replyTo=reply_to
        )
    )


@router.post("/{comment_id}/like", response_model=ApiResponse[LikeResponse])
@limiter.limit("30/minute")
async def toggle_like_comment(
    request: Request,
    comment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    点赞/取消点赞评论
    
    - 基于客户端IP判断是否已点赞
    - 切换点赞状态（已点赞则取消，未点赞则添加）
    """
    # 验证UUID格式
    try:
        uuid.UUID(comment_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的评论ID格式"
        )
    
    # 查询评论是否存在
    comment_query = select(Comment).where(Comment.id == comment_id, Comment.is_deleted == False)
    comment_result = await db.execute(comment_query)
    comment = comment_result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在"
        )
    
    client_ip = get_client_ip(request)
    
    # 检查是否已点赞
    like_query = select(CommentLike).where(
        CommentLike.comment_id == comment_id,
        CommentLike.client_ip == client_ip
    )
    like_result = await db.execute(like_query)
    existing_like = like_result.scalar_one_or_none()
    
    if existing_like:
        # 已点赞，取消点赞
        await db.delete(existing_like)
        new_likes = max(0, comment.likes - 1)
        is_liked = False
    else:
        # 未点赞，添加点赞
        new_like = CommentLike(
            id=str(uuid.uuid4()),
            comment_id=comment_id,
            client_ip=client_ip,
            created_at=datetime.now()
        )
        db.add(new_like)
        new_likes = comment.likes + 1
        is_liked = True
    
    # 更新评论点赞数
    update_query = update(Comment).where(Comment.id == comment_id).values(likes=new_likes)
    await db.execute(update_query)
    await db.commit()
    
    logger.info(f"评论点赞状态切换: {comment_id}, isLiked={is_liked}, from {client_ip}")
    
    return ApiResponse(
        code=200,
        message="操作成功",
        data=LikeResponse(
            isLiked=is_liked,
            likes=new_likes
        )
    )
