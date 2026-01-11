"""
时区工具模块
统一使用北京时间 (UTC+8)
"""
from datetime import datetime, timezone, timedelta

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


def now_beijing() -> datetime:
    """
    获取当前北京时间
    
    返回不带时区信息的 datetime 对象，直接存入数据库
    """
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)


def to_beijing(dt: datetime) -> datetime:
    """
    将 UTC 时间转换为北京时间
    
    Args:
        dt: UTC 时间（带或不带时区信息）
    
    Returns:
        北京时间（不带时区信息）
    """
    if dt.tzinfo is None:
        # 假设是 UTC 时间
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.astimezone(BEIJING_TZ).replace(tzinfo=None)
