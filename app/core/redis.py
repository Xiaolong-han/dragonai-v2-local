import asyncio
import json
import logging
import random
from typing import Optional, Any, Callable
from functools import wraps
from datetime import datetime
import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)

# 空值缓存标记
NULL_VALUE_MARKER = "__NULL__"


def is_sqlalchemy_model(obj: Any) -> bool:
    return hasattr(obj, '__table__')


def model_to_dict(obj: Any) -> Any:
    if isinstance(obj, list):
        return [model_to_dict(item) for item in obj]
    
    if not is_sqlalchemy_model(obj):
        return obj
    
    data = {}
    for column in obj.__table__.columns:
        column_name = column.name
        try:
            value = None
            
            if column_name == 'metadata':
                if hasattr(obj, 'metadata_'):
                    value = getattr(obj, 'metadata_')
                else:
                    value = None
            else:
                try:
                    value = getattr(obj, column_name)
                except AttributeError:
                    value = None
            
            if isinstance(value, datetime):
                data[column_name] = value.isoformat()
            elif value is not None:
                if isinstance(value, (str, int, float, bool, list, dict)):
                    data[column_name] = value
                else:
                    try:
                        data[column_name] = json.dumps(value)
                    except (TypeError, ValueError):
                        data[column_name] = None
            else:
                data[column_name] = None
        except Exception:
            data[column_name] = None
    return data


class RedisClient:
    def __init__(self):
        self.redis_url = settings.redis_url
        self._client: Optional[redis.Redis] = None

    async def connect(self):
        if self._client is None:
            self._client = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)

    async def disconnect(self):
        if self._client:
            await self._client.close()
            self._client = None

    async def close(self):
        """关闭 Redis 连接（兼容方法）"""
        await self.disconnect()

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client

    async def get(self, key: str) -> Optional[Any]:
        value = await self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        if is_sqlalchemy_model(value) or (isinstance(value, list) and value and is_sqlalchemy_model(value[0])):
            value = model_to_dict(value)
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await self.client.set(key, value, ex=ttl)

    async def delete(self, key: str):
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        return await self.client.exists(key) > 0

    async def acquire_lock(self, lock_key: str, expire_seconds: int = 10) -> bool:
        """获取分布式锁"""
        return await self.client.set(lock_key, "1", nx=True, ex=expire_seconds)

    async def release_lock(self, lock_key: str):
        """释放分布式锁"""
        await self.client.delete(lock_key)


redis_client = RedisClient()


async def cache_aside(
    key: str,
    ttl: int = 3600,
    data_func: Optional[Callable] = None,
    enable_null_cache: bool = True,
    null_cache_ttl: int = 300,
    enable_lock: bool = True,
    lock_expire_seconds: int = 10,
    enable_random_ttl: bool = True,
    random_ttl_range: int = 300,
    *args,
    **kwargs
) -> Any:
    """
    Cache-Aside 模式实现，包含防穿透、防击穿、防雪崩机制
    
    Args:
        key: 缓存键
        ttl: 缓存过期时间（秒）
        data_func: 数据获取函数
        enable_null_cache: 是否启用空值缓存（防穿透）
        null_cache_ttl: 空值缓存过期时间（秒）
        enable_lock: 是否启用互斥锁（防击穿）
        lock_expire_seconds: 锁过期时间（秒）
        enable_random_ttl: 是否启用随机TTL（防雪崩）
        random_ttl_range: 随机TTL范围（秒）
    """
    # 1. 先查缓存
    cached = await redis_client.get(key)
    if cached is not None:
        # 检查是否是空值标记（防穿透）
        if cached == NULL_VALUE_MARKER:
            logger.info(f"[CACHE HIT NULL] 空值缓存命中: {key}")
            return None
        logger.info(f"[CACHE HIT] 数据从缓存获取: {key}")
        return cached

    # 2. 缓存未命中，尝试获取互斥锁（防击穿）
    if enable_lock:
        lock_key = f"lock:{key}"
        lock_acquired = await redis_client.acquire_lock(lock_key, lock_expire_seconds)
        
        if not lock_acquired:
            # 其他线程正在加载，等待后重试
            logger.info(f"[CACHE LOCK] 等待其他线程加载: {key}")
            await asyncio.sleep(0.1)
            return await cache_aside(
                key, ttl, data_func,
                enable_null_cache, null_cache_ttl,
                enable_lock, lock_expire_seconds,
                enable_random_ttl, random_ttl_range,
                *args, **kwargs
            )
        
        try:
            # 双重检查
            cached = await redis_client.get(key)
            if cached is not None:
                if cached == NULL_VALUE_MARKER:
                    logger.info(f"[CACHE HIT NULL] 空值缓存命中(双重检查): {key}")
                    return None
                logger.info(f"[CACHE HIT] 数据从缓存获取(双重检查): {key}")
                return cached
        except Exception:
            pass

    logger.info(f"[CACHE MISS] 缓存未命中，从数据库获取: {key}")
    
    if data_func is None:
        if enable_lock:
            await redis_client.release_lock(lock_key)
        return None

    try:
        # 3. 从数据库获取数据
        data = await data_func(*args, **kwargs)
        
        # 4. 计算实际 TTL（防雪崩）
        actual_ttl = ttl
        if enable_random_ttl:
            actual_ttl = ttl + random.randint(0, random_ttl_range)
        
        # 5. 回填缓存
        if data is not None:
            await redis_client.set(key, data, ttl=actual_ttl)
            logger.info(f"[CACHE SET] 数据已写入缓存: {key}, TTL={actual_ttl}s")
        else:
            # 空值缓存（防穿透）
            if enable_null_cache:
                await redis_client.set(key, NULL_VALUE_MARKER, ttl=null_cache_ttl)
                logger.info(f"[CACHE SET NULL] 空值已写入缓存: {key}, TTL={null_cache_ttl}s")
        
        return data
    finally:
        # 6. 释放锁
        if enable_lock:
            await redis_client.release_lock(lock_key)


def cached(ttl: int = 3600, key_prefix: str = "cache"):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            key = ":".join(key_parts)

            return await cache_aside(key=key, ttl=ttl, data_func=func, *args, **kwargs)

        return wrapper
    return decorator
