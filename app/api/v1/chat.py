import asyncio
import json
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.message import (
    MessageResponse,
    ChatRequest,
    ChatHistoryResponse,
    MessageCreate
)
from app.services.chat_service import chat_service
from app.services.conversation_service import conversation_service

router = APIRouter(prefix="/chat", tags=["聊天"])
logger = logging.getLogger(__name__)


@router.get("/conversations/{conversation_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    conversation_id: int,
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=500, description="返回数量"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    conv = await conversation_service.get_conversation(db, conversation_id=conversation_id, user_id=current_user.id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = await chat_service.get_messages(
        db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return ChatHistoryResponse(messages=messages, total=len(messages))


@router.post("/send")
async def send_chat_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    conv = await conversation_service.get_conversation(
        db,
        conversation_id=chat_request.conversation_id,
        user_id=current_user.id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    await chat_service.create_message(
        db,
        conversation_id=chat_request.conversation_id,
        message_create=MessageCreate(
            role="user",
            content=chat_request.content,
            metadata={"images": chat_request.images} if chat_request.images else None
        ),
        user_id=current_user.id
    )
    
    messages_history = await chat_service.get_messages(
        db,
        conversation_id=chat_request.conversation_id,
        user_id=current_user.id,
        limit=50
    )
    history = [{"role": m.role, "content": m.content} for m in messages_history]
    
    if chat_request.stream:
        async def generate():
            full_response = ""
            thinking_content = ""
            chunk_count = 0
            async for event in chat_service.generate_response_stream(
                conversation_id=chat_request.conversation_id,
                user_id=current_user.id,
                content=chat_request.content,
                model_type=chat_request.model_type,
                is_expert=chat_request.is_expert,
                enable_thinking=chat_request.enable_thinking,
                images=chat_request.images,
                messages_history=history[:-1]
            ):
                if isinstance(event, dict):
                    if event.get("type") == "thinking":
                        thinking_data = event.get("data", {})
                        thinking_content += thinking_data.get("content", "")
                        logger.info(f"[SSE] Sending thinking event, content length: {len(thinking_data.get('content', ''))}")
                        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    elif event.get("type") == "thinking_end":
                        logger.info(f"[SSE] Sending thinking_end event")
                        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    elif event.get("type") == "content":
                        content_data = event.get("data", {})
                        content = content_data.get("content", "")
                        full_response += content
                        logger.info(f"[SSE] Sending content event: {content[:50]}...")
                        yield f"data: {json.dumps(content, ensure_ascii=False)}\n\n"
                    else:
                        content = event.get("content", "")
                        full_response += content
                        yield f"data: {json.dumps(content, ensure_ascii=False)}\n\n"
                else:
                    full_response += event
                    chunk_count += 1
                    logger.info(f"[SSE] Sending chunk {chunk_count}: {len(event)} chars")
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)
            
            logger.info(f"[SSE] Stream complete, total chunks: {chunk_count}, total chars: {len(full_response)}")
            logger.info(f"[SSE] Full response content:\n{full_response}")
            logger.info(f"[SSE] Thinking content length: {len(thinking_content)}")
            
            metadata = {"model": "expert" if chat_request.is_expert else "fast"}
            if thinking_content:
                metadata["thinking_content"] = thinking_content
                logger.info(f"[SSE] Saving thinking_content to metadata, length: {len(thinking_content)}")
            
            await chat_service.create_message(
                db,
                conversation_id=chat_request.conversation_id,
                message_create=MessageCreate(
                    role="assistant",
                    content=full_response,
                    metadata=metadata
                ),
                user_id=current_user.id
            )
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Content-Type": "text/event-stream; charset=utf-8"
            }
        )
    else:
        response = await chat_service.generate_response(
            conversation_id=chat_request.conversation_id,
            user_id=current_user.id,
            content=chat_request.content,
            model_type=chat_request.model_type,
            is_expert=chat_request.is_expert,
            enable_thinking=chat_request.enable_thinking,
            images=chat_request.images,
            messages_history=history[:-1]
        )
        
        await chat_service.create_message(
            db,
            conversation_id=chat_request.conversation_id,
            message_create=MessageCreate(
                role="assistant",
                content=response,
                metadata={"model": "expert" if chat_request.is_expert else "fast"}
            ),
            user_id=current_user.id
        )
        
        return {"response": response}
