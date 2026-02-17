import logging
from typing import List
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
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
        
        db = SessionLocal()
        try:
            # 获取需要预热的用户列表（活跃用户）
            active_users = db.query(User).limit(50).all()
            
            for user in active_users:
                user_id = user.id
                
                # 预热该用户的会话列表缓存
                cache_key = f"conversations:user:{user_id}:skip:0:limit:100"
                
                async def fetch_conversations():
                    return db.query(Conversation).filter(
                        Conversation.user_id == user_id
                    ).order_by(
                        Conversation.is_pinned.desc(),
                        Conversation.updated_at.desc()
                    ).offset(0).limit(100).all()
                
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
            
        finally:
            db.close()
    
    @staticmethod
    async def warmup_pinned_conversations():
        """预热置顶会话详情缓存"""
        logger.info("[CACHE WARMUP] 开始预热置顶会话详情缓存")
        
        db = SessionLocal()
        try:
            # 获取所有置顶会话
            pinned_conversations = db.query(Conversation).filter(
                Conversation.is_pinned == True
            ).all()
            
            for conv in pinned_conversations:
                user_id = conv.user_id
                conversation_id = conv.id
                
                cache_key = f"conversation:{conversation_id}:{user_id}"
                
                async def fetch_conversation():
                    return db.query(Conversation).filter(
                        Conversation.id == conversation_id,
                        Conversation.user_id == user_id
                    ).first()
                
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
            
        finally:
            db.close()
    
    @staticmethod
    async def warmup_recent_conversations(hours: int = 24):
        """
        预热最近活跃的会话
        
        Args:
            hours: 预热最近多少小时内有更新的会话
        """
        from datetime import datetime, timedelta
        
        logger.info(f"[CACHE WARMUP] 开始预热最近 {hours} 小时活跃的会话")
        
        db = SessionLocal()
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # 获取最近活跃的会话
            recent_conversations = db.query(Conversation).filter(
                Conversation.updated_at >= cutoff_time
            ).limit(200).all()
            
            for conv in recent_conversations:
                user_id = conv.user_id
                conversation_id = conv.id
                
                # 预热会话详情
                cache_key = f"conversation:{conversation_id}:{user_id}"
                
                async def fetch_conversation():
                    return db.query(Conversation).filter(
                        Conversation.id == conversation_id,
                        Conversation.user_id == user_id
                    ).first()
                
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
            
        finally:
            db.close()
    
    @staticmethod
    async def warmup_all():
        """执行所有缓存预热"""
        logger.info("[CACHE WARMUP] ========== 开始缓存预热 ==========")
        
        await CacheWarmup.warmup_conversations(limit=100)
        await CacheWarmup.warmup_pinned_conversations()
        await CacheWarmup.warmup_recent_conversations(hours=24)
        
        logger.info("[CACHE WARMUP] ========== 缓存预热完成 ==========")


# 全局缓存预热实例
cache_warmup = CacheWarmup()
