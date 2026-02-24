
import logging
from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.schemas.conversation import ConversationCreate, ConversationUpdate
from app.core.redis import redis_client, cache_aside
from app.services.chat_service import chat_service

logger = logging.getLogger(__name__)


class ConversationService:
    @staticmethod
    async def get_conversation(db: AsyncSession, conversation_id: int, user_id: int) -> Optional[Conversation]:
        cache_key = f"conversation:{conversation_id}:{user_id}"
        
        async def fetch():
            result = await db.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id
                )
            )
            return result.scalar_one_or_none()
        
        conv = await cache_aside(key=cache_key, ttl=3600, data_func=fetch)
        return conv

    @staticmethod
    async def get_conversations(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[Conversation]:
        cache_key = f"conversations:user:{user_id}:skip:{skip}:limit:{limit}"
        
        async def fetch():
            result = await db.execute(
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(desc(Conversation.is_pinned), desc(Conversation.updated_at))
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        
        return await cache_aside(key=cache_key, ttl=3600, data_func=fetch)

    @staticmethod
    async def create_conversation(db: AsyncSession, conversation: ConversationCreate, user_id: int) -> Conversation:
        db_conv = Conversation(
            user_id=user_id,
            title=conversation.title,
            model_name=conversation.model_name,
            is_pinned=False
        )
        db.add(db_conv)
        await db.flush()
        await db.refresh(db_conv)
        
        await ConversationService._invalidate_user_cache(user_id)
        return db_conv

    @staticmethod
    async def update_conversation(
        db: AsyncSession,
        conversation_id: int,
        conversation_update: ConversationUpdate,
        user_id: int
    ) -> Optional[Conversation]:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        conv = result.scalar_one_or_none()
        if not conv:
            return None
        
        update_data = conversation_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(conv, field, value)
        
        await db.flush()
        await db.refresh(conv)
        
        await ConversationService._invalidate_conversation_cache(conversation_id, user_id)
        await ConversationService._invalidate_user_cache(user_id)
        return conv

    @staticmethod
    async def delete_conversation(db: AsyncSession, conversation_id: int, user_id: int) -> bool:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        conv = result.scalar_one_or_none()
        if not conv:
            return False
        
        await db.delete(conv)
        await db.flush()
        
        await ConversationService._invalidate_conversation_cache(conversation_id, user_id)
        await ConversationService._invalidate_user_cache(user_id)
        await chat_service._invalidate_messages_cache(conversation_id, user_id)
        return True

    @staticmethod
    async def pin_conversation(db: AsyncSession, conversation_id: int, user_id: int, pinned: bool) -> Optional[Conversation]:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        conv = result.scalar_one_or_none()
        if not conv:
            return None
        
        conv.is_pinned = pinned
        await db.flush()
        await db.refresh(conv)
        
        await ConversationService._invalidate_conversation_cache(conversation_id, user_id)
        await ConversationService._invalidate_user_cache(user_id)
        return conv

    @staticmethod
    async def _invalidate_user_cache(user_id: int):
        pattern = f"conversations:user:{user_id}:*"
        cursor = 0
        all_keys = []
        while True:
            cursor, keys = await redis_client.client.scan(cursor, match=pattern, count=100)
            all_keys.extend(keys)
            if cursor == 0:
                break
        
        if all_keys:
            await redis_client.client.delete(*all_keys)
            logger.info(f"[CACHE DELETE] 已删除用户会话列表缓存: user_id={user_id}, keys={len(all_keys)}")
        else:
            logger.info(f"[CACHE DELETE] 未找到用户会话列表缓存: user_id={user_id}")

    @staticmethod
    async def _invalidate_conversation_cache(conversation_id: int, user_id: int):
        cache_key = f"conversation:{conversation_id}:{user_id}"
        exists = await redis_client.exists(cache_key)
        if exists:
            await redis_client.delete(cache_key)
            logger.info(f"[CACHE DELETE] 已删除会话缓存: conversation_id={conversation_id}")


conversation_service = ConversationService()
