
import logging
from typing import List, Optional
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.schemas.conversation import ConversationCreate, ConversationUpdate
from app.core.redis import redis_client, cache_aside
from app.services.chat_service import chat_service

logger = logging.getLogger(__name__)


class ConversationService:
    @staticmethod
    async def get_conversation(db: Session, conversation_id: int, user_id: int) -> Optional[Conversation]:
        cache_key = f"conversation:{conversation_id}:{user_id}"
        
        async def fetch():
            return db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            ).first()
        
        conv = await cache_aside(key=cache_key, ttl=3600, data_func=fetch)
        return conv

    @staticmethod
    async def get_conversations(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Conversation]:
        cache_key = f"conversations:user:{user_id}:skip:{skip}:limit:{limit}"
        
        async def fetch():
            return db.query(Conversation).filter(
                Conversation.user_id == user_id
            ).order_by(
                desc(Conversation.is_pinned),
                desc(Conversation.updated_at)
            ).offset(skip).limit(limit).all()
        
        return await cache_aside(key=cache_key, ttl=3600, data_func=fetch)

    @staticmethod
    async def create_conversation(db: Session, conversation: ConversationCreate, user_id: int) -> Conversation:
        db_conv = Conversation(
            user_id=user_id,
            title=conversation.title,
            model_name=conversation.model_name,
            is_pinned=False
        )
        db.add(db_conv)
        db.commit()
        db.refresh(db_conv)
        
        await ConversationService._invalidate_user_cache(user_id)
        return db_conv

    @staticmethod
    async def update_conversation(
        db: Session,
        conversation_id: int,
        conversation_update: ConversationUpdate,
        user_id: int
    ) -> Optional[Conversation]:
        conv = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
        if not conv:
            return None
        
        update_data = conversation_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(conv, field, value)
        
        db.commit()
        db.refresh(conv)
        
        await ConversationService._invalidate_conversation_cache(conversation_id, user_id)
        await ConversationService._invalidate_user_cache(user_id)
        return conv

    @staticmethod
    async def delete_conversation(db: Session, conversation_id: int, user_id: int) -> bool:
        conv = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
        if not conv:
            return False
        
        db.delete(conv)
        db.commit()
        
        await ConversationService._invalidate_conversation_cache(conversation_id, user_id)
        await ConversationService._invalidate_user_cache(user_id)
        await chat_service._invalidate_messages_cache(conversation_id, user_id)
        return True

    @staticmethod
    async def pin_conversation(db: Session, conversation_id: int, user_id: int, pinned: bool) -> Optional[Conversation]:
        conv = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
        if not conv:
            return None
        
        conv.is_pinned = pinned
        db.commit()
        db.refresh(conv)
        
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
            logger.info(f"[CACHE DELETE] 已删除会话缓存: {cache_key}")
        else:
            logger.info(f"[CACHE DELETE] 会话缓存不存在: {cache_key}")


conversation_service = ConversationService()
