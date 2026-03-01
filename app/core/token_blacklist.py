"""Token 黑名单管理"""

import logging
import time
from typing import Optional

from app.core.redis import redis_client
from app.core.security import decode_access_token

logger = logging.getLogger(__name__)


class TokenBlacklist:
    """Token 黑名单管理
    
    使用 Redis 存储已撤销的 Token，支持：
    - 登出时将 Token 加入黑名单
    - 验证时检查 Token 是否在黑名单中
    - 自动过期（TTL 与 Token 过期时间一致）
    """
    
    PREFIX = "token_blacklist:"
    
    @classmethod
    async def add(cls, token: str) -> bool:
        """将 Token 加入黑名单
        
        Args:
            token: JWT Token 字符串
            
        Returns:
            是否成功加入黑名单
        """
        payload = decode_access_token(token)
        if not payload:
            logger.warning("[TOKEN BLACKLIST] Invalid token, cannot add to blacklist")
            return False
        
        jti = payload.get("jti") or payload.get("sub")
        exp = payload.get("exp", 0)
        
        current_time = int(time.time())
        ttl = max(exp - current_time, 0)
        
        if ttl <= 0:
            logger.debug(f"[TOKEN BLACKLIST] Token already expired, skip: jti={jti}")
            return True
        
        key = f"{cls.PREFIX}{jti}"
        await redis_client.set(key, "1", ttl=ttl)
        logger.info(f"[TOKEN BLACKLIST] Added to blacklist: jti={jti}, ttl={ttl}s")
        return True
    
    @classmethod
    async def is_blacklisted(cls, token: str) -> bool:
        """检查 Token 是否在黑名单中
        
        Args:
            token: JWT Token 字符串
            
        Returns:
            是否在黑名单中
        """
        payload = decode_access_token(token)
        if not payload:
            return True
        
        jti = payload.get("jti") or payload.get("sub")
        key = f"{cls.PREFIX}{jti}"
        
        exists = await redis_client.exists(key)
        return exists
    
    @classmethod
    async def remove(cls, token: str) -> bool:
        """从黑名单中移除 Token（用于测试或特殊场景）
        
        Args:
            token: JWT Token 字符串
            
        Returns:
            是否成功移除
        """
        payload = decode_access_token(token)
        if not payload:
            return False
        
        jti = payload.get("jti") or payload.get("sub")
        key = f"{cls.PREFIX}{jti}"
        
        await redis_client.delete(key)
        logger.info(f"[TOKEN BLACKLIST] Removed from blacklist: jti={jti}")
        return True
    
    @classmethod
    async def get_ttl(cls, token: str) -> Optional[int]:
        """获取 Token 黑名单的剩余 TTL
        
        Args:
            token: JWT Token 字符串
            
        Returns:
            剩余秒数，如果不在黑名单中返回 None
        """
        payload = decode_access_token(token)
        if not payload:
            return None
        
        jti = payload.get("jti") or payload.get("sub")
        key = f"{cls.PREFIX}{jti}"
        
        client = redis_client.client
        ttl = await client.ttl(key)
        
        if ttl > 0:
            return ttl
        return None
