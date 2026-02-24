"""缓存监控模块"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class CacheMetrics:
    """缓存指标收集器"""
    
    def __init__(self):
        self._hits = 0
        self._misses = 0
        self._null_hits = 0
        self._errors = 0
        self._start_time = datetime.now()
    
    def record_hit(self):
        self._hits += 1
    
    def record_miss(self):
        self._misses += 1
    
    def record_null_hit(self):
        self._null_hits += 1
    
    def record_error(self):
        self._errors += 1
    
    def get_stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses + self._null_hits
        hit_rate = (self._hits + self._null_hits) / total * 100 if total > 0 else 0
        
        return {
            "hits": self._hits,
            "misses": self._misses,
            "null_hits": self._null_hits,
            "errors": self._errors,
            "total_requests": total,
            "hit_rate": round(hit_rate, 2),
            "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
        }
    
    def reset(self):
        self._hits = 0
        self._misses = 0
        self._null_hits = 0
        self._errors = 0
        self._start_time = datetime.now()


cache_metrics = CacheMetrics()


async def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计信息"""
    from app.core.redis import redis_client
    
    stats = cache_metrics.get_stats()
    
    try:
        info = await redis_client.client.info("memory")
        stats["redis_memory_used"] = info.get("used_memory_human", "unknown")
        stats["redis_memory_peak"] = info.get("used_memory_peak_human", "unknown")
        
        info_stats = await redis_client.client.info("stats")
        stats["redis_total_commands"] = info_stats.get("total_commands_processed", 0)
        stats["redis_connections_received"] = info_stats.get("total_connections_received", 0)
        
        dbsize = await redis_client.client.dbsize()
        stats["redis_key_count"] = dbsize
    except Exception as e:
        logger.warning(f"[CACHE METRICS] 无法获取 Redis 信息: {e}")
        stats["redis_error"] = str(e)
    
    return stats
