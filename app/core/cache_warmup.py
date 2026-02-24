import logging
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.redis import redis_client, cache_aside
from app.models.conversation import Conversation
from app.models.user import User

logger = logging.getLogger(__name__)


class CacheWarmup:
    """缓存预热服务"""
    
    @staticmethod
    async def warmup_conversations(limit: int = 100):
        """
        预热会话列表缓存
        
        预热策略：
        1. 预热置顶会话
        2. 预热最近更新的会话
        """
        logger.info(f"[CACHE WARMUP] 开始预热会话列表缓存，限制 {limit} 条")
        
        async with get_db_session() as db:
            result = await db.execute(select(User).limit(50))
            active_users = result.scalars().all()
            
            for user in active_users:
                user_id = user.id
                
                cache_key = f"conversations:user:{user_id}:skip:0:limit:100"
                
                async def fetch_conversations():
                    result = await db.execute(
                        select(Conversation)
                        .where(Conversation.user_id == user_id)
                        .order_by(Conversation.is_pinned.desc(), Conversation.updated_at.desc())
                        .offset(0)
                        .limit(100)
                    )
                    return result.scalars().all()
                
                try:
                    await cache_aside(
                        key=cache_key,
                        ttl=3600,
                        data_func=fetch_conversations,
                        enable_null_cache=True,
                        enable_lock=True,
                        enable_random_ttl=True
                    )
                    logger.info(f"[CACHE WARMUP] 用户 {user_id} 的会话列表已预热")
                except Exception as e:
                    logger.error(f"[CACHE WARMUP] 预热用户 {user_id} 会话列表失败: {e}")
            
            logger.info(f"[CACHE WARMUP] 会话列表缓存预热完成，预热了 {len(active_users)} 个用户")
    
    @staticmethod
    async def warmup_pinned_conversations():
        """预热置顶会话详情缓存"""
        logger.info("[CACHE WARMUP] 开始预热置顶会话详情缓存")
        
        async with get_db_session() as db:
            result = await db.execute(
                select(Conversation).where(Conversation.is_pinned == True)
            )
            pinned_conversations = result.scalars().all()
            
            for conv in pinned_conversations:
                user_id = conv.user_id
                conversation_id = conv.id
                
                cache_key = f"conversation:{conversation_id}:{user_id}"
                
                async def fetch_conversation():
                    result = await db.execute(
                        select(Conversation)
                        .where(
                            Conversation.id == conversation_id,
                            Conversation.user_id == user_id
                        )
                    )
                    return result.scalar_one_or_none()
                
                try:
                    await cache_aside(
                        key=cache_key,
                        ttl=3600,
                        data_func=fetch_conversation,
                        enable_null_cache=True,
                        enable_lock=True,
                        enable_random_ttl=True
                    )
                    logger.info(f"[CACHE WARMUP] 置顶会话 {conversation_id} 已预热")
                except Exception as e:
                    logger.error(f"[CACHE WARMUP] 预热置顶会话 {conversation_id} 失败: {e}")
            
            logger.info(f"[CACHE WARMUP] 置顶会话详情缓存预热完成，预热了 {len(pinned_conversations)} 个会话")
    
    @staticmethod
    async def warmup_recent_conversations(hours: int = 24):
        """
        预热最近活跃的会话
        
        Args:
            hours: 预热最近多少小时内有更新的会话
        """
        from datetime import datetime, timedelta
        
        logger.info(f"[CACHE WARMUP] 开始预热最近 {hours} 小时活跃的会话")
        
        async with get_db_session() as db:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            result = await db.execute(
                select(Conversation)
                .where(Conversation.updated_at >= cutoff_time)
                .limit(200)
            )
            recent_conversations = result.scalars().all()
            
            for conv in recent_conversations:
                user_id = conv.user_id
                conversation_id = conv.id
                
                cache_key = f"conversation:{conversation_id}:{user_id}"
                
                async def fetch_conversation():
                    result = await db.execute(
                        select(Conversation)
                        .where(
                            Conversation.id == conversation_id,
                            Conversation.user_id == user_id
                        )
                    )
                    return result.scalar_one_or_none()
                
                try:
                    await cache_aside(
                        key=cache_key,
                        ttl=3600,
                        data_func=fetch_conversation,
                        enable_null_cache=True,
                        enable_lock=True,
                        enable_random_ttl=True
                    )
                except Exception as e:
                    logger.error(f"[CACHE WARMUP] 预热会话 {conversation_id} 失败: {e}")
            
            logger.info(f"[CACHE WARMUP] 最近活跃会话缓存预热完成，预热了 {len(recent_conversations)} 个会话")
    
    @staticmethod
    async def warmup_all():
        """执行所有缓存预热"""
        logger.info("[CACHE WARMUP] ========== 开始缓存预热 ==========")
        
        await CacheWarmup.warmup_conversations(limit=100)
        await CacheWarmup.warmup_pinned_conversations()
        await CacheWarmup.warmup_recent_conversations(hours=24)
        
        logger.info("[CACHE WARMUP] ========== 缓存预热完成 ==========")


cache_warmup = CacheWarmup()
