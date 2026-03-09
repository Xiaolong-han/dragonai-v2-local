import json
import asyncio
import logging
from typing import AsyncGenerator, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.stream.stream_processor import StreamProcessor
from app.services.repositories.message_repository import MessageRepository
from app.schemas.message import MessageCreate

logger = logging.getLogger(__name__)


class SSEEmitter:
    """SSE 输出器，负责生成 SSE 格式的流式响应"""
    
    def __init__(
        self,
        stream_processor: Optional[StreamProcessor] = None,
        message_repository: Optional[MessageRepository] = None
    ):
        self.stream_processor = stream_processor or StreamProcessor()
        self.message_repository = message_repository or MessageRepository()
    
    @staticmethod
    def make_sse_event(event_type: str, content: str = "") -> str:
        """生成 SSE 格式的事件"""
        return f"data: {json.dumps({'type': event_type, 'data': {'content': content}}, ensure_ascii=False)}\n\n"
    
    async def generate_sse_stream(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        content: str,
        is_expert: bool = False,
        enable_thinking: bool = False,
        attachments: Optional[List[str]] = None
    ) -> AsyncGenerator[str, None]:
        """生成 SSE 格式的流式响应
        
        封装了完整的 SSE 流式响应逻辑，包括：
        - 调用 StreamProcessor 获取原始流
        - 转换为 SSE 格式
        - 累积响应并保存到数据库
        """
        full_response = ""
        thinking_content = ""
        chunk_count = 0
        tool_calls = []
        
        try:
            async for event in self.stream_processor.process_message(
                conversation_id=conversation_id,
                content=content,
                user_id=user_id,
                attachments=attachments,
                is_expert=is_expert,
                enable_thinking=enable_thinking
            ):
                if isinstance(event, dict):
                    event_type = event.get("type")
                    logger.debug(f"[SSE] Processing event: type={event_type}")
                    
                    if event_type == "thinking":
                        thinking_chunk = event.get("data", {}).get("content", "")
                        thinking_content += thinking_chunk
                        logger.debug(f"[SSE] Sending thinking chunk: {len(thinking_chunk)} chars")
                        yield self.make_sse_event("thinking", thinking_chunk)
                        
                    elif event_type == "thinking_end":
                        logger.debug(f"[SSE] Sending thinking_end")
                        yield self.make_sse_event("thinking_end")
                        
                    elif event_type == "token":
                        token_content = event.get("data", {}).get("content", "")
                        if token_content:
                            full_response += token_content
                            chunk_count += 1
                            logger.debug(f"[SSE] Sending chunk {chunk_count}: {len(token_content)} chars")
                            yield self.make_sse_event("content", token_content)
                    
                    elif event_type == "tool_call":
                        calls = event.get("data", {}).get("calls", [])
                        for call in calls:
                            tool_id = call.get("id", "")
                            if tool_id:
                                placeholder = f"[TOOL_CALL:{tool_id}]"
                                full_response += placeholder
                                yield self.make_sse_event("content", placeholder)
                            tool_calls.append({
                                "id": call.get("id", ""),
                                "name": call.get("name", ""),
                                "status": "pending"
                            })
                        yield self.make_sse_event("tool_call", json.dumps({"calls": calls}, ensure_ascii=False))
                    
                    elif event_type == "tool_result":
                        data = event.get("data", {})
                        tool_call_id = data.get("tool_call_id")
                        for tc in tool_calls:
                            if tc.get("id") == tool_call_id:
                                tc["status"] = "success"
                                tc["summary"] = data.get("summary", "")
                                tc["links"] = data.get("links", [])
                                tc["details"] = data.get("details", "")
                                break
                        yield self.make_sse_event("tool_result", json.dumps(data, ensure_ascii=False))
                    
                    elif event_type == "error":
                        yield self.make_sse_event("error", event.get("data", {}).get("message", ""))
                        
                else:
                    full_response += event
                    chunk_count += 1
                    logger.debug(f"[SSE] Sending chunk {chunk_count}: {len(event)} chars")
                    yield self.make_sse_event("content", event)
                await asyncio.sleep(0.01)
            
            logger.info(f"[SSE] Stream complete, total chunks: {chunk_count}, response length: {len(full_response)}")
            
            if thinking_content:
                logger.debug(f"[SSE] Sending thinking_end, total thinking: {len(thinking_content)} chars")
                yield self.make_sse_event("thinking_end")
            
            extra_data = {"model": "expert" if is_expert else "fast"}
            if thinking_content:
                extra_data["thinking_content"] = thinking_content
            if tool_calls:
                extra_data["tool_calls"] = tool_calls
            
            await self.message_repository.create_message(
                db,
                conversation_id=conversation_id,
                message_create=MessageCreate(
                    role="assistant",
                    content=full_response,
                    extra_data=extra_data
                ),
                user_id=user_id
            )
            yield "data: [DONE]\n\n"
        except asyncio.CancelledError:
            logger.info(f"[SSE] Request cancelled, conversation_id={conversation_id}")
            raise
