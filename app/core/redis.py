
import json
from typing import Optional, Any, Callable
from functools import wraps
import redis.asyncio as redis

from app.config import settings


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
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await self.client.set(key, value, ex=ttl)

    async def delete(self, key: str):
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        return await self.client.exists(key) > 0


redis_client = RedisClient()


async def cache_aside(
    key: str,
    ttl: int = 3600,
    data_func: Optional[Callable] = None,
    *args,
    **kwargs
) -> Any:
    cached = await redis_client.get(key)
    if cached is not None:
        return cached

    if data_func is None:
        return None

    data = await data_func(*args, **kwargs)
    if data is not None:
        await redis_client.set(key, data, ttl=ttl)
    return data


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

