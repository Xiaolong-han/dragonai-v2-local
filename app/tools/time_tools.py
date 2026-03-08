"""时间工具 - 获取当前时间"""

from datetime import datetime
from zoneinfo import ZoneInfo
from langchain_core.tools import tool


@tool
def get_current_time(timezone: str = None) -> str:
    """
    获取当前日期和时间。

    当用户询问当前时间、日期、星期几时使用此工具。

    Args:
        timezone: 时区名称，如 'Asia/Shanghai', 'UTC', 'America/New_York'。
                  默认使用本地时区。

    Returns:
        当前时间的格式化字符串，包含日期、时间、星期、时区信息
    """
    if timezone:
        try:
            tz = ZoneInfo(timezone)
            now = datetime.now(tz)
        except Exception:
            now = datetime.now()
            return f"无效的时区 '{timezone}'，返回本地时间：{now.strftime('%Y-%m-%d %H:%M:%S')} (星期{['一','二','三','四','五','六','日'][now.weekday()]})"
    else:
        now = datetime.now()
    
    weekdays = ['一', '二', '三', '四', '五', '六', '日']
    weekday = weekdays[now.weekday()]
    
    tz_name = now.tzinfo.tzname(now) if now.tzinfo else "本地时区"
    
    return f"{now.strftime('%Y-%m-%d %H:%M:%S')} (星期{weekday}) [{tz_name}]"
