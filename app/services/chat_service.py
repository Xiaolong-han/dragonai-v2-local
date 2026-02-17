
import logging
from typing import List, Optional, AsyncGenerator, Dict, Any
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.message import Message
from app.models.conversation import Conversation
from app.schemas.message import MessageCreate
from app.core.redis import redis_client, cache_aside
from app.llm.model_factory import ModelFactory
from app.config import settings

logger = logging.getLogger(__name__)


class ChatService:
    @staticmethod
    async def get_messages(
        db: Session,
        conversation_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        cache_key = f"messages:conversation:{conversation_id}:user:{user_id}:skip:{skip}:limit:{limit}"
        
        async def fetch():
            return db.query(Message).join(
                Conversation, Message.conversation_id == Conversation.id
            ).filter(
                Message.conversation_id == conversation_id,
                Conversation.user_id == user_id
            ).order_by(
                desc(Message.created_at)
            ).offset(skip).limit(limit).all()
        
        messages = await cache_aside(key=cache_key, ttl=3600, data_func=fetch)
        return list(reversed(messages)) if messages else []

    @staticmethod
    async def create_message(
        db: Session,
        conversation_id: int,
        message_create: MessageCreate,
        user_id: int
    ) -> Optional[Message]:
        conv = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
        if not conv:
            return None
        
        db_message = Message(
            conversation_id=conversation_id,
            role=message_create.role,
            content=message_create.content,
            metadata_=message_create.metadata_
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        
        await ChatService._invalidate_messages_cache(conversation_id, user_id)
        return db_message

    @staticmethod
    async def generate_response_stream(
        conversation_id: int,
        user_id: int,
        content: str,
        model_type: str = "general",
        is_expert: bool = False,
        images: Optional[List[str]] = None,
        messages_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[str, None]:
        if model_type == "vision" and images:
            model = ModelFactory.get_vision_model(
                is_ocr=False,
                stream=True,
                temperature=0.7
            )
            prompt = content
            if images:
                for img_url in images:
                    prompt += f"\n![image]({img_url})"
        else:
            model = ModelFactory.get_general_model(
                is_expert=is_expert,
                stream=True,
                temperature=0.7
            )
            prompt = content
        
        messages = []
        if messages_history:
            messages.extend(messages_history)
        messages.append({"role": "user", "content": prompt})
        
        try:
            async for chunk in model.astream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    @staticmethod
    async def generate_response(
        conversation_id: int,
        user_id: int,
        content: str,
        model_type: str = "general",
        is_expert: bool = False,
        images: Optional[List[str]] = None,
        messages_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        if model_type == "vision" and images:
            model = ModelFactory.get_vision_model(
                is_ocr=False,
                stream=False,
                temperature=0.7
            )
            prompt = content
            if images:
                for img_url in images:
                    prompt += f"\n![image]({img_url})"
        else:
            model = ModelFactory.get_general_model(
                is_expert=is_expert,
                stream=False,
                temperature=0.7
            )
            prompt = content
        
        messages = []
        if messages_history:
            messages.extend(messages_history)
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await model.ainvoke(messages)
            return response.content if response else ""
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    async def _invalidate_messages_cache(conversation_id: int, user_id: int):
        pattern = f"messages:conversation:{conversation_id}:user:{user_id}:*"
        cursor = 0
        all_keys = []
        while True:
            cursor, keys = await redis_client.client.scan(cursor, match=pattern, count=100)
            all_keys.extend(keys)
            if cursor == 0:
                break
        
        if all_keys:
            await redis_client.client.delete(*all_keys)
            logger.info(f"[CACHE DELETE] 已删除消息缓存: conversation_id={conversation_id}, user_id={user_id}, keys={len(all_keys)}")
        else:
            logger.info(f"[CACHE DELETE] 未找到消息缓存: conversation_id={conversation_id}, user_id={user_id}")


chat_service = ChatService()

