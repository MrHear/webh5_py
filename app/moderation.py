"""
内容审核模块
使用 DeepSeek API 进行评论文明检测
包含本地敏感词预过滤 + AI 深度检测
使用 Redis 存储每日调用计数
"""
import asyncio
import httpx
from datetime import date
from typing import Tuple, Optional
from loguru import logger
import redis.asyncio as redis

from sqlalchemy import update

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models import Comment


# ============== Redis 连接 ==============
_redis_client: Optional[redis.Redis] = None
_redis_available: bool = True  # Redis 是否可用的标记


async def get_redis() -> Optional[redis.Redis]:
    """获取 Redis 连接（单例），带超时和优雅降级"""
    global _redis_client, _redis_available
    
    # 如果之前检测到 Redis 不可用，直接返回 None
    if not _redis_available:
        return None
    
    if _redis_client is None:
        settings = get_settings()
        try:
            logger.debug(f"[Redis] 尝试连接: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            # 使用显式参数而非 URL，避免密码解析问题
            _redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_timeout=3,
                socket_connect_timeout=3
            )
            # 测试连接
            await _redis_client.ping()
            logger.info("[Redis] 连接成功")
        except asyncio.TimeoutError:
            logger.warning("[Redis] 连接超时，降级为本地计数")
            _redis_available = False
            _redis_client = None
            return None
        except Exception as e:
            logger.warning(f"[Redis] 连接失败({type(e).__name__})，降级为本地计数: {e}")
            _redis_available = False
            _redis_client = None
            return None
    
    return _redis_client


# 本地计数器（Redis 不可用时的后备方案）
_local_daily_calls = {"date": None, "count": 0}


# ============== 本地敏感词预过滤 ==============
# 包含这些词的评论会被送去 AI 审核，其他直接通过
SENSITIVE_KEYWORDS = [
    # 脏话/辱骂
    "傻逼", "sb", "操", "草", "妈", "爸", "日", "艹", "fuck", "shit", "damn",
    "狗", "猪", "蠢", "白痴", "弱智", "智障", "脑残", "废物", "垃圾", "滚",
    "死", "杀", "打", "揍",
    # 色情
    "性", "裸", "色情", "约炮", "一夜情", "援交",
    # 广告
    "加微信", "加qq", "加v", "威信", "薇信", "私聊", "优惠", "免费领",
    "点击链接", "http://", "https://", ".com", ".cn", ".top",
    # 政治敏感（简化）
    "政府", "领导", "官员",
]


def _get_daily_key() -> str:
    """获取今日的 Redis 计数器 key"""
    return f"moderation:daily_count:{date.today().isoformat()}"


async def _check_daily_limit() -> bool:
    """检查是否超过每日限额，返回 True 表示可以调用"""
    settings = get_settings()
    
    r = await get_redis()
    if r:
        # 使用 Redis
        try:
            key = _get_daily_key()
            count = await r.get(key)
            current = int(count) if count else 0
            return current < settings.MODERATION_DAILY_LIMIT
        except Exception as e:
            logger.warning(f"[审核] Redis 读取失败: {e}")
    
    # 降级：使用本地计数器
    today = date.today()
    if _local_daily_calls["date"] != today:
        _local_daily_calls["date"] = today
        _local_daily_calls["count"] = 0
    
    return _local_daily_calls["count"] < settings.MODERATION_DAILY_LIMIT


async def _increment_api_calls() -> int:
    """增加 API 调用计数，返回当前计数"""
    r = await get_redis()
    if r:
        # 使用 Redis
        try:
            key = _get_daily_key()
            count = await r.incr(key)
            # 设置过期时间为 25 小时（确保跨天后自动清理）
            await r.expire(key, 90000)
            return count
        except Exception as e:
            logger.warning(f"[审核] Redis 写入失败: {e}")
    
    # 降级：使用本地计数器
    today = date.today()
    if _local_daily_calls["date"] != today:
        _local_daily_calls["date"] = today
        _local_daily_calls["count"] = 0
    
    _local_daily_calls["count"] += 1
    return _local_daily_calls["count"]


def contains_sensitive_words(content: str) -> bool:
    """检查内容是否包含敏感词"""
    content_lower = content.lower()
    for word in SENSITIVE_KEYWORDS:
        if word.lower() in content_lower:
            return True
    return False


# 审核提示词 (注意: 大括号需要双写来转义)
MODERATION_PROMPT = """你是一个内容审核助手。请判断以下用户评论是否符合文明规范。

需要检测的内容类型：
1. 辱骂、攻击性言论
2. 色情、低俗内容
3. 广告、垃圾信息
4. 政治敏感内容
5. 其他违规内容

用户评论内容：
"{content}"

请用JSON格式回复：
- 如果内容合规，回复：{{"pass": true, "reason": ""}}
- 如果内容违规，回复：{{"pass": false, "reason": "简短说明违规原因"}}

只需要回复JSON，不要其他内容。"""


async def check_content_with_deepseek(content: str) -> Tuple[bool, str]:
    """
    使用 DeepSeek API 检测内容是否合规
    
    Args:
        content: 待检测的内容
        
    Returns:
        (is_pass, reason): 是否通过, 原因
    """
    settings = get_settings()
    
    if not settings.DEEPSEEK_API_KEY:
        logger.warning("DeepSeek API Key 未配置，跳过内容审核")
        return True, ""
    
    try:
        async with httpx.AsyncClient(timeout=settings.MODERATION_TIMEOUT) as client:
            response = await client.post(
                settings.DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.DEEPSEEK_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": MODERATION_PROMPT.format(content=content)
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 100
                }
            )
            
            if response.status_code != 200:
                logger.error(f"DeepSeek API 调用失败: {response.status_code} - {response.text}")
                return True, ""  # API 失败时默认通过
            
            result = response.json()
            reply = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            logger.info(f"[审核] DeepSeek 原始返回: {repr(reply)}")
            
            # 解析返回的 JSON
            import json
            import re
            
            # 尝试提取 JSON 部分
            reply = reply.strip()
            
            # 移除 markdown 代码块标记
            if reply.startswith("```"):
                lines = reply.split("\n")
                reply = "\n".join(lines[1:-1] if lines[-1].strip() in ["```", "```json"] else lines[1:])
                reply = reply.strip()
            
            # 尝试用正则提取 JSON 对象
            json_match = re.search(r'\{[^{}]*\}', reply)
            if json_match:
                reply = json_match.group()
            
            logger.info(f"[审核] 准备解析: {repr(reply)}")
            
            try:
                data = json.loads(reply)
            except json.JSONDecodeError as e:
                logger.warning(f"[审核] JSON解析失败: {e}")
                return True, ""
            
            logger.info(f"[审核] 解析结果: type={type(data).__name__}, value={data}")
            
            # 确保 data 是字典类型
            if not isinstance(data, dict):
                logger.warning(f"[审核] 结果不是字典，跳过")
                return True, ""
            
            is_pass = data.get("pass", True)
            reason = data.get("reason", "")
            
            logger.info(f"[审核] pass={is_pass} (type={type(is_pass).__name__}), reason={reason}")
            
            # 确保 is_pass 是布尔值
            if isinstance(is_pass, str):
                is_pass = is_pass.lower() in ("true", "1", "yes")
            
            return bool(is_pass), str(reason)
                
    except httpx.TimeoutException:
        logger.warning(f"DeepSeek API 超时")
        return True, ""  # 超时时默认通过
    except Exception as e:
        import traceback
        logger.error(f"内容审核异常: {e}\n{traceback.format_exc()}")
        return True, ""  # 异常时默认通过


async def moderate_comment(comment_id: str, content: str):
    """
    异步审核评论内容
    
    审核策略:
    1. 内容过短 → 直接通过
    2. 不包含敏感词 → 直接通过
    3. 超过每日限额 → 直接通过（保护 Token）
    4. 包含敏感词 → 调用 AI 审核
    
    Args:
        comment_id: 评论ID
        content: 评论内容
    """
    settings = get_settings()
    
    if not settings.MODERATION_ENABLED:
        logger.debug(f"内容审核已禁用，跳过评论 {comment_id}")
        return
    
    # 1. 本地敏感词预检测
    has_sensitive = contains_sensitive_words(content)
    
    if not has_sensitive:
        # 不包含敏感词，直接通过
        logger.info(f"[审核] 未检测到敏感词，直接通过: {comment_id}")
        await _update_comment_status(comment_id, "approved", None)
        return
    
    # 2. 包含敏感词，检查每日 API 调用限额
    if not await _check_daily_limit():
        logger.warning(f"[审核] 已达每日限额({settings.MODERATION_DAILY_LIMIT})，跳过: {comment_id}")
        await _update_comment_status(comment_id, "approved", None)
        return
    
    logger.info(f"[审核] 检测到敏感词，调用 AI 审核: {comment_id}")
    
    # 3. 调用 DeepSeek 检测
    current_count = await _increment_api_calls()
    is_pass, reason = await check_content_with_deepseek(content)
    
    logger.info(f"[审核] 今日已调用 API: {current_count}/{settings.MODERATION_DAILY_LIMIT}")

    # 更新审核状态
    if is_pass:
        logger.info(f"评论审核通过: {comment_id}")
        await _update_comment_status(comment_id, "approved", None)
    else:
        logger.warning(f"评论审核不通过: {comment_id}, 原因: {reason}")
        await _update_comment_status(comment_id, "rejected", reason)


async def _update_comment_status(comment_id: str, status: str, reason: Optional[str]):
    """更新评论审核状态"""
    try:
        async with AsyncSessionLocal() as db:
            stmt = update(Comment).where(Comment.id == comment_id).values(
                moderation_status=status,
                moderation_reason=reason
            )
            await db.execute(stmt)
            await db.commit()
    except Exception as e:
        logger.error(f"更新审核状态失败: {comment_id}, 错误: {e}")


def trigger_moderation(comment_id: str, content: str):
    """
    触发异步审核任务
    
    在后台线程中执行，不阻塞主请求
    """
    asyncio.create_task(moderate_comment(comment_id, content))
