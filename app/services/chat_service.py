
import logging
import json
import asyncio
from typing import List, Optional, AsyncGenerator, Dict, Any, Union
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.models.conversation import Conversation
from app.schemas.message import MessageCreate
from app.core.redis import redis_client, cache_aside
from app.llm.model_factory import ModelFactory
from app.config import settings

logger = logging.getLogger(__name__)

AGENT_TIMEOUT = 300


class ChatService:
    @staticmethod
    async def get_messages(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        cache_key = f"messages:conversation:{conversation_id}:user:{user_id}:skip:{skip}:limit:{limit}"
        
        async def fetch():
            result = await db.execute(
                select(Message)
                .join(Conversation, Message.conversation_id == Conversation.id)
                .where(
                    Message.conversation_id == conversation_id,
                    Conversation.user_id == user_id
                )
                .order_by(Message.created_at.asc())
                .offset(skip)
                .limit(limit)
            )
            messages = result.scalars().all()
            return messages
        
        messages = await cache_aside(key=cache_key, ttl=3600, data_func=fetch)
        return messages if messages else []

    @staticmethod
    async def create_message(
        db: AsyncSession,
        conversation_id: int,
        message_create: MessageCreate,
        user_id: int
    ) -> Optional[Message]:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        conv = result.scalar_one_or_none()
        if not conv:
            return None
        
        db_message = Message(
            conversation_id=conversation_id,
            role=message_create.role,
            content=message_create.content,
            metadata_=message_create.metadata_
        )
        db.add(db_message)
        await db.flush()
        await db.refresh(db_message)
        
        logger.debug(f"[DB] Saved message id={db_message.id}")
        
        verify_result = await db.execute(
            select(Message).where(Message.id == db_message.id)
        )
        verify_msg = verify_result.scalar_one_or_none()
        if verify_msg:
            logger.debug(f"[DB] Verify saved: id={verify_msg.id}")
        
        await ChatService._invalidate_messages_cache(conversation_id, user_id)
        return db_message

    @staticmethod
    async def process_message(
        conversation_id: int,
        content: str,
        images: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        is_expert: bool = False,
        enable_thinking: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理用户消息 - 支持多模态输入和Agent工具调用

        使用LangChain 1.0+的create_agent，通过stream_mode="values"获取流式输出。
        使用PostgresSaver实现对话状态持久化。
        """
        try:
            logger.info(f"[CHAT] 开始处理消息: conversation_id={conversation_id}")

            context_parts = [content]

            if images:
                for img in images:
                    context_parts.append(f"[图片路径: {img}]")

            if files:
                for file in files:
                    doc_content = await ChatService._extract_document_content(file)
                    context_parts.append(f"[文档内容: {doc_content}]")

            full_context = "\n\n".join(context_parts)
            logger.debug(f"[CHAT] 上下文准备完成，长度: {len(full_context)}")

            from app.agents.agent_factory import AgentFactory
            logger.debug(f"[CHAT] 创建Agent: is_expert={is_expert}, enable_thinking={enable_thinking}")
            agent = AgentFactory.create_chat_agent(
                is_expert=is_expert,
                enable_thinking=enable_thinking
            )

            config = AgentFactory.get_agent_config(str(conversation_id))

            logger.debug(f"[CHAT] 开始流式执行Agent")
            tool_call_count = 0
            
            async def _process_stream():
                nonlocal tool_call_count
                async for stream_mode, data in agent.astream(
                    {"messages": [{"role": "user", "content": full_context}]},
                    config,
                    stream_mode=["messages", "updates"]
                ):
                    if stream_mode == "messages":
                        message, metadata = data
                        formatted = ChatService._format_stream_message(message, metadata, enable_thinking)
                        if formatted:
                            yield formatted
                    elif stream_mode == "updates":
                        logger.debug(f"[CHAT-DEBUG] updates data: {data}")
                        for source, update in data.items():
                            logger.debug(f"[CHAT-DEBUG] source={source}, update keys={update.keys() if isinstance(update, dict) else type(update)}")
                            if source in ("model", "tools"):
                                formatted_list = ChatService._format_update({source: update}, enable_thinking)
                                for formatted in formatted_list:
                                    if formatted.get("type") == "tool_call":
                                        tool_call_count += 1
                                        if tool_call_count > 5:
                                            logger.error(f"[CHAT] 工具调用过多，强制停止")
                                            return
                                    if formatted.get("type") not in ("unknown", None):
                                        yield formatted
            
            try:
                async with asyncio.timeout(AGENT_TIMEOUT):
                    async for event in _process_stream():
                        yield event
            except asyncio.TimeoutError:
                logger.error(f"[CHAT] Agent执行超时，conversation_id={conversation_id}")
                yield {"type": "error", "data": {"message": "请求处理超时，请稍后重试"}}
                return

            logger.info(f"[CHAT] Agent流式执行完成")
        except Exception as e:
            error_msg = str(e)
            if "tool_calls" in error_msg and "must be followed by tool messages" in error_msg:
                logger.warning(f"[CHAT] 检测到无效的tool_calls，清理对话状态并重试")
                from app.agents.agent_factory import AgentFactory
                await AgentFactory.reset_conversation_state(str(conversation_id))
                
                try:
                    agent = AgentFactory.create_chat_agent(
                        is_expert=is_expert,
                        enable_thinking=enable_thinking
                    )
                    config = AgentFactory.get_agent_config(str(conversation_id))
                    
                    async with asyncio.timeout(AGENT_TIMEOUT):
                        async for stream_mode, data in agent.astream(
                            {"messages": [{"role": "user", "content": full_context}]},
                            config,
                            stream_mode=["messages", "updates"]
                        ):
                            if stream_mode == "messages":
                                message, metadata = data
                                formatted = ChatService._format_stream_message(message, metadata, enable_thinking)
                                if formatted:
                                    yield formatted
                            elif stream_mode == "updates":
                                for source, update in data.items():
                                    if source in ("model", "tools"):
                                        formatted_list = ChatService._format_update({source: update}, enable_thinking)
                                        for formatted in formatted_list:
                                            if formatted.get("type") not in ("unknown", None):
                                                yield formatted
                    logger.info(f"[CHAT] 重试执行成功")
                    return
                except asyncio.TimeoutError:
                    logger.error(f"[CHAT] 重试执行超时，conversation_id={conversation_id}")
                    yield {"type": "error", "data": {"message": "请求处理超时，请稍后重试"}}
                    return
                except Exception as retry_error:
                    logger.error(f"[CHAT] 重试执行失败: {str(retry_error)}")
                    yield {"type": "error", "data": {"message": str(retry_error)}}
                    return
            
            logger.error(f"[CHAT] 处理消息时出错: {str(e)}", exc_info=True)
            yield {"type": "error", "data": {"message": str(e)}}

    @staticmethod
    def _format_stream_message(message, metadata, include_thinking: bool) -> Optional[Dict[str, Any]]:
        """格式化流式消息（stream_mode="messages"）
        
        message: AIMessageChunk 或 ToolMessage
        metadata: 包含 langgraph_node 等信息
        
        注意：工具调用信息在 updates 模式下处理，这里只处理文本 token
        """
        from langchain_core.messages.ai import AIMessageChunk
        from langchain_core.messages.tool import ToolMessage
        
        if isinstance(message, AIMessageChunk):
            tool_call_chunks = getattr(message, 'tool_call_chunks', None)
            if tool_call_chunks:
                return None
            
            content = getattr(message, 'content', "")
            
            if include_thinking:
                thinking_content = None
                
                if hasattr(message, 'content_blocks') and message.content_blocks:
                    for block in message.content_blocks:
                        if isinstance(block, dict):
                            if block.get('type') == 'reasoning':
                                thinking_content = block.get('reasoning', '')
                            elif block.get('type') == 'thinking':
                                thinking_content = block.get('thinking', '')
                
                if not thinking_content and hasattr(message, 'additional_kwargs'):
                    additional_kwargs = message.additional_kwargs or {}
                    if 'reasoning_content' in additional_kwargs:
                        thinking_content = additional_kwargs['reasoning_content']
                    elif 'thinking' in additional_kwargs:
                        thinking_content = additional_kwargs['thinking']
                    elif 'reasoning' in additional_kwargs:
                        reasoning = additional_kwargs['reasoning']
                        if isinstance(reasoning, dict) and 'summary' in reasoning:
                            thinking_content = ''.join([
                                s.get('text', '') for s in reasoning['summary'] 
                                if s.get('type') == 'summary_text'
                            ])
                
                if not thinking_content and isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            if item.get('type') == 'thinking':
                                thinking_content = item.get('thinking', '')
                            elif item.get('type') == 'reasoning':
                                thinking_content = item.get('reasoning', '')
                            if thinking_content:
                                break
                
                if thinking_content:
                    return {
                        "type": "thinking",
                        "data": {"content": thinking_content}
                    }
            
            if content and not isinstance(content, list):
                return {
                    "type": "token",
                    "data": {"content": content}
                }
        
        elif isinstance(message, ToolMessage):
            return None
        
        return None

    @staticmethod
    def _format_update(event: Dict, include_thinking: bool) -> List[Dict[str, Any]]:
        """格式化更新事件（stream_mode="updates"）
        
        event 格式: {"model": {"messages": [...]}} 或 {"tools": {"messages": [...]}}
        
        返回事件列表，可能包含 thinking 和 content 两个事件
        """
        results = []
        for node_name, node_output in event.items():
            if node_name in ("model", "agent"):
                messages = node_output.get("messages", []) if isinstance(node_output, dict) else []
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, 'type'):
                        if last_message.type == "ai":
                            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                                tool_names = [tc.get('name', '') for tc in last_message.tool_calls]
                                tool_names = [n for n in tool_names if n]
                                if tool_names:
                                    return [{
                                        "type": "tool_call",
                                        "data": {"names": tool_names}
                                    }]
                            
                            content = getattr(last_message, 'content', "")
                            thinking_content = None
                            
                            if include_thinking:
                                if hasattr(last_message, 'content_blocks') and last_message.content_blocks:
                                    for block in last_message.content_blocks:
                                        if isinstance(block, dict):
                                            if block.get('type') == 'reasoning':
                                                thinking_content = block.get('reasoning', '')
                                            elif block.get('type') == 'thinking':
                                                thinking_content = block.get('thinking', '')
                                
                                if not thinking_content and hasattr(last_message, 'additional_kwargs'):
                                    additional_kwargs = last_message.additional_kwargs or {}
                                    if 'reasoning_content' in additional_kwargs:
                                        thinking_content = additional_kwargs['reasoning_content']
                                    elif 'thinking' in additional_kwargs:
                                        thinking_content = additional_kwargs['thinking']
                                    elif 'reasoning' in additional_kwargs:
                                        reasoning = additional_kwargs['reasoning']
                                        if isinstance(reasoning, dict) and 'summary' in reasoning:
                                            thinking_content = ''.join([
                                                s.get('text', '') for s in reasoning['summary'] 
                                                if s.get('type') == 'summary_text'
                                            ])
                                
                                if not thinking_content and isinstance(content, list):
                                    for item in content:
                                        if isinstance(item, dict):
                                            if item.get('type') == 'thinking':
                                                thinking_content = item.get('thinking', '')
                                            elif item.get('type') == 'reasoning':
                                                thinking_content = item.get('reasoning', '')
                                            if thinking_content:
                                                break
                            
                            if thinking_content:
                                results.append({
                                    "type": "thinking",
                                    "data": {"content": thinking_content}
                                })
                            
                            if isinstance(content, list):
                                text_content = ""
                                for item in content:
                                    if isinstance(item, dict) and item.get('type') == 'text':
                                        text_content += item.get('text', '')
                                    elif isinstance(item, str):
                                        text_content += item
                                if text_content:
                                    results.append({
                                        "type": "content",
                                        "data": {"content": text_content}
                                    })
                            elif content:
                                results.append({
                                    "type": "content",
                                    "data": {"content": content}
                                })
                            
                            return results if results else []
            elif node_name == "tools":
                messages = node_output.get("messages", []) if isinstance(node_output, dict) else []
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, 'type') and last_message.type == "tool":
                        tool_name = getattr(last_message, 'name', None)
                        tool_content = getattr(last_message, 'content', None)
                        return [{
                            "type": "tool_result",
                            "data": {
                                "name": tool_name,
                                "content": tool_content
                            }
                        }]
        return [{"type": "unknown", "data": event}]

    @staticmethod
    def _format_event(event: Dict, include_thinking: bool) -> Dict[str, Any]:
        """格式化Agent事件为前端可消费的格式"""
        messages = event.get("messages", [])
        if not messages:
            return {"type": "unknown", "data": event}

        last_message = messages[-1]

        if hasattr(last_message, 'type'):
            message_type = last_message.type

            if message_type == "ai":
                content = last_message.content if hasattr(last_message, 'content') else ""

                thinking_content = None
                if include_thinking:
                    thinking_content = getattr(last_message, 'thinking_content', None) or \
                                       getattr(last_message, 'reasoning_content', None)

                return {
                    "type": "content",
                    "data": {
                        "content": content,
                        "thinking_content": thinking_content
                    }
                }

            elif message_type == "tool":
                return {
                    "type": "tool_call",
                    "data": {
                        "name": getattr(last_message, 'name', None),
                        "content": getattr(last_message, 'content', None)
                    }
                }

            elif message_type == "human":
                return {"type": "human", "data": {"content": getattr(last_message, 'content', None)}}

        elif isinstance(last_message, dict):
            message_type = last_message.get("type", "")

            if message_type == "ai":
                content = last_message.get("content", "")
                thinking_content = None
                if include_thinking:
                    thinking_content = last_message.get("thinking_content") or \
                                       last_message.get("reasoning_content")

                return {
                    "type": "content",
                    "data": {
                        "content": content,
                        "thinking_content": thinking_content
                    }
                }

            elif message_type == "tool":
                return {
                    "type": "tool_call",
                    "data": {
                        "name": last_message.get("name"),
                        "content": last_message.get("content")
                    }
                }

        return {"type": "unknown", "data": event}

    @staticmethod
    async def _extract_document_content(file_path: str) -> str:
        """提取文档内容"""
        return ""

    @staticmethod
    async def generate_response_stream(
        conversation_id: int,
        user_id: int,
        content: str,
        model_type: str = "general",
        is_expert: bool = False,
        enable_thinking: bool = False,
        images: Optional[List[str]] = None,
        messages_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[Union[str, Dict[str, Any]], None]:
        """使用Agent生成流式响应
        
        Args:
            enable_thinking: 是否启用深度思考模式，启用时会流式输出思考内容
        """
        try:
            logger.debug(f"[CHAT] 开始生成流式响应: conversation_id={conversation_id}, enable_thinking={enable_thinking}")
            has_token_output = False
            in_thinking_mode = False
            async for event in ChatService.process_message(
                conversation_id=conversation_id,
                content=content,
                images=images,
                is_expert=is_expert,
                enable_thinking=enable_thinking
            ):
                if event["type"] == "token":
                    token_content = event["data"]["content"]
                    if token_content:
                        has_token_output = True
                        yield token_content
                elif event["type"] == "content":
                    if not has_token_output:
                        content_data = event["data"].get("content")
                        if content_data:
                            yield event
                elif event["type"] == "thinking":
                    in_thinking_mode = True
                    yield event
                elif event["type"] == "thinking_end":
                    in_thinking_mode = False
                    yield event
                elif event["type"] == "tool_call":
                    names = [n for n in event["data"].get("names", []) if n]
                    if names:
                        yield f"\n[使用工具: {', '.join(names)}]\n"
                elif event["type"] == "tool_result":
                    pass
        except Exception as e:
            logger.error(f"[CHAT] 生成流式响应时出错: {str(e)}", exc_info=True)
            yield f"\n[Error: {str(e)}]"

    @staticmethod
    async def generate_response(
        conversation_id: int,
        user_id: int,
        content: str,
        model_type: str = "general",
        is_expert: bool = False,
        enable_thinking: bool = False,
        images: Optional[List[str]] = None,
        messages_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """使用Agent生成非流式响应"""
        try:
            full_response = []
            async for event in ChatService.process_message(
                conversation_id=conversation_id,
                content=content,
                images=images,
                is_expert=is_expert,
                enable_thinking=enable_thinking
            ):
                if event["type"] == "content":
                    full_response.append(event["data"]["content"])
                elif event["type"] == "tool_call":
                    full_response.append(f"\n[使用工具: {event['data']['name']}]\n")
                elif event["type"] == "error":
                    return f"Error: {event['data'].get('message', 'Unknown error')}"

            return "".join(full_response)
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
            logger.debug(f"[CACHE DELETE] 已删除消息缓存: conversation_id={conversation_id}, keys={len(all_keys)}")


chat_service = ChatService()
