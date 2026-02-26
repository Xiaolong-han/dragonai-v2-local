import asyncio
import json
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.rate_limit import limiter, CHAT_RATE_LIMIT
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
@limiter.limit(CHAT_RATE_LIMIT)
async def get_chat_history(
    request: Request,
    conversation_id: int,
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=500, description="返回数量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
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
@limiter.limit(CHAT_RATE_LIMIT)
async def send_chat_message(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
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
            metadata_={"images": chat_request.images} if chat_request.images else None
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
                    logger.debug(f"[SSE] Processing event: type={event.get('type')}")
                    if event.get("type") == "thinking":
                        thinking_chunk = event.get("data", {}).get("content", "")
                        thinking_content += thinking_chunk
                        logger.debug(f"[SSE] Sending thinking chunk: {len(thinking_chunk)} chars")
                        yield f"data: {json.dumps({'type': 'thinking', 'data': {'content': thinking_chunk}}, ensure_ascii=False)}\n\n"
                    elif event.get("type") == "thinking_end":
                        logger.debug(f"[SSE] Sending thinking_end")
                        yield f"data: {json.dumps({'type': 'thinking_end', 'data': {'content': ''}}, ensure_ascii=False)}\n\n"
                    else:
                        content = event.get("data", {}).get("content", "") or event.get("content", "")
                        full_response += content
                        yield f"data: {json.dumps({'type': 'content', 'data': {'content': content}}, ensure_ascii=False)}\n\n"
                else:
                    full_response += event
                    chunk_count += 1
                    logger.debug(f"[SSE] Sending chunk {chunk_count}: {len(event)} chars")
                    yield f"data: {json.dumps({'type': 'content', 'data': {'content': event}}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)
            
            logger.info(f"[SSE] Stream complete, total chunks: {chunk_count}, response length: {len(full_response)}")
            
            if thinking_content:
                logger.debug(f"[SSE] Sending thinking_end, total thinking: {len(thinking_content)} chars")
                yield f"data: {json.dumps({'type': 'thinking_end', 'data': {'content': ''}}, ensure_ascii=False)}\n\n"
            
            metadata = {"model": "expert" if chat_request.is_expert else "fast"}
            if thinking_content:
                metadata["thinking_content"] = thinking_content
            
            await chat_service.create_message(
                db,
                conversation_id=chat_request.conversation_id,
                message_create=MessageCreate(
                    role="assistant",
                    content=full_response,
                    metadata_=metadata
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
                metadata_={"model": "expert" if chat_request.is_expert else "fast"}
            ),
            user_id=current_user.id
        )
        
        return {"response": response}
