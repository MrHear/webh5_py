"""
文章路由模块
处理所有文章相关的API请求
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_db
from app.models import Post
from app.schemas import (
    PostCreate, PostUpdate, PostDetail, PostInList,
    PostCreateResponse, ApiResponse, PaginatedData, PostType
)
from app.security import require_admin
from app.rate_limiter import limiter

router = APIRouter(prefix="/posts", tags=["文章"])


@router.get("", response_model=ApiResponse[PaginatedData[PostInList]])
@limiter.limit("30/minute")
async def get_posts(
    request: Request,
    page: int = Query(1, ge=1, le=1000, description="页码"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    type: Optional[PostType] = Query(None, description="文章类型筛选"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取文章列表
    
    - 支持分页
    - 支持按类型筛选
    - 返回摘要信息，不含正文
    """
    # 构建基础查询
    base_query = select(Post).where(Post.is_deleted == False)
    
    # 类型筛选
    if type:
        base_query = base_query.where(Post.type == type.value)
    
    # 查询总数
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    offset = (page - 1) * limit
    posts_query = base_query.order_by(Post.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(posts_query)
    posts = result.scalars().all()
    
    # 转换为响应格式
    post_list = [
        PostInList(
            id=post.id,
            title=post.title,
            summary=post.summary,
            type=post.type,
            tags=post.tags or [],
            views=post.views,
            createdAt=post.created_at
        )
        for post in posts
    ]
    
    return ApiResponse(
        code=200,
        message="success",
        data=PaginatedData(
            total=total,
            page=page,
            list=post_list
        )
    )


@router.get("/{post_id}", response_model=ApiResponse[PostDetail])
@limiter.limit("60/minute")
async def get_post(
    request: Request,
    post_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取文章详情
    
    - 返回完整文章内容
    - 自动增加阅读量
    """
    # 验证UUID格式
    try:
        uuid.UUID(post_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的文章ID格式"
        )
    
    # 查询文章
    query = select(Post).where(Post.id == post_id, Post.is_deleted == False)
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在"
        )
    
    # 增加阅读量
    update_query = update(Post).where(Post.id == post_id).values(views=Post.views + 1)
    await db.execute(update_query)
    await db.commit()
    
    return ApiResponse(
        code=200,
        message="success",
        data=PostDetail(
            id=post.id,
            title=post.title,
            summary=post.summary,
            content=post.content,
            type=post.type,
            tags=post.tags or [],
            views=post.views,  # 返回更新后的阅读量
            createdAt=post.created_at
        )
    )


@router.post("", response_model=ApiResponse[PostCreateResponse], status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_post(
    request: Request,
    post_data: PostCreate,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(require_admin)
):
    """
    创建新文章
    
    - 需要管理员权限
    - 自动生成UUID
    - 输入内容会被安全过滤
    """
    logger.info(f"管理员 {admin} 正在创建新文章: {post_data.title}")
    
    # 生成UUID
    post_id = str(uuid.uuid4())
    
    # 创建文章记录
    new_post = Post(
        id=post_id,
        title=post_data.title,
        summary=post_data.summary,
        content=post_data.content,
        type=post_data.type.value,
        tags=post_data.tags,
        views=0,
        created_at=datetime.now()
    )
    
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    
    logger.info(f"文章创建成功: {post_id}")
    
    return ApiResponse(
        code=201,
        message="文章发布成功",
        data=PostCreateResponse(
            id=post_id,
            createdAt=new_post.created_at
        )
    )


@router.put("/{post_id}", response_model=ApiResponse[PostDetail])
@limiter.limit("20/minute")
async def update_post(
    request: Request,
    post_id: str,
    post_data: PostUpdate,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(require_admin)
):
    """
    更新文章
    
    - 需要管理员权限
    - 支持部分更新
    """
    # 验证UUID格式
    try:
        uuid.UUID(post_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的文章ID格式"
        )
    
    # 查询文章
    query = select(Post).where(Post.id == post_id, Post.is_deleted == False)
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在"
        )
    
    # 更新字段
    update_data = post_data.model_dump(exclude_unset=True)
    if "type" in update_data and update_data["type"]:
        update_data["type"] = update_data["type"].value
    
    for key, value in update_data.items():
        setattr(post, key, value)
    
    await db.commit()
    await db.refresh(post)
    
    logger.info(f"管理员 {admin} 更新了文章: {post_id}")
    
    return ApiResponse(
        code=200,
        message="文章更新成功",
        data=PostDetail(
            id=post.id,
            title=post.title,
            summary=post.summary,
            content=post.content,
            type=post.type,
            tags=post.tags or [],
            views=post.views,
            createdAt=post.created_at
        )
    )


@router.delete("/{post_id}", response_model=ApiResponse)
@limiter.limit("10/minute")
async def delete_post(
    request: Request,
    post_id: str,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(require_admin)
):
    """
    删除文章（软删除）
    
    - 需要管理员权限
    - 使用软删除，数据不会真正删除
    """
    # 验证UUID格式
    try:
        uuid.UUID(post_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的文章ID格式"
        )
    
    # 查询文章
    query = select(Post).where(Post.id == post_id, Post.is_deleted == False)
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在"
        )
    
    # 软删除
    post.is_deleted = True
    await db.commit()
    
    logger.info(f"管理员 {admin} 删除了文章: {post_id}")
    
    return ApiResponse(
        code=200,
        message="文章删除成功",
        data=None
    )
