
import logging
import json
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

            # 1. 处理多模态输入
            context_parts = [content]

            if images:
                for img in images:
                    vision_model = ModelFactory.get_vision_model()
                    image_understanding = await vision_model.aunderstand_image(img)
                    context_parts.append(f"[图片内容: {image_understanding}]")

            if files:
                for file in files:
                    doc_content = await ChatService._extract_document_content(file)
                    context_parts.append(f"[文档内容: {doc_content}]")

            full_context = "\n\n".join(context_parts)
            logger.info(f"[CHAT] 上下文准备完成，长度: {len(full_context)}")

            # 2. 创建Agent
            # 延迟导入避免循环导入
            from app.agents.agent_factory import AgentFactory
            logger.info(f"[CHAT] 创建Agent: is_expert={is_expert}, enable_thinking={enable_thinking}")
            agent = AgentFactory.create_chat_agent(
                is_expert=is_expert,
                enable_thinking=enable_thinking
            )
            logger.info(f"[CHAT] Agent创建成功")

            # 3. 获取Agent配置（用于对话状态持久化）
            config = AgentFactory.get_agent_config(str(conversation_id))
            logger.info(f"[CHAT] Agent配置: {config}")

            # 4. 流式执行Agent (LangChain 1.0+ 方式)
            # 使用 stream_mode="messages" 获取流式 token 输出
            logger.info(f"[CHAT] 开始流式执行Agent")
            async for message, metadata in agent.astream(
                {"messages": [{"role": "user", "content": full_context}]},
                config,  # 传入config实现对话状态持久化
                stream_mode="messages"
            ):
                formatted = ChatService._format_stream_message(message, metadata, enable_thinking)
                if formatted:
                    yield formatted

            logger.info(f"[CHAT] Agent流式执行完成")
        except Exception as e:
            logger.error(f"[CHAT] 处理消息时出错: {str(e)}", exc_info=True)
            yield {"type": "error", "data": {"message": str(e)}}

    @staticmethod
    def _format_stream_message(message, metadata, include_thinking: bool) -> Optional[Dict[str, Any]]:
        """格式化流式消息（stream_mode="messages"）
        
        message: AIMessageChunk 或 ToolMessage
        metadata: 包含 langgraph_node 等信息
        """
        from langchain_core.messages.ai import AIMessageChunk
        from langchain_core.messages.tool import ToolMessage
        
        # 检查消息类型
        if isinstance(message, AIMessageChunk):
            # AI 消息块（流式 token）
            content = getattr(message, 'content', "")
            if content:
                return {
                    "type": "token",
                    "data": {"content": content}
                }
        elif isinstance(message, ToolMessage):
            # 工具调用消息
            tool_name = getattr(message, 'name', 'unknown')
            return {
                "type": "tool_call",
                "data": {"name": tool_name}
            }
        
        return None

    @staticmethod
    def _format_update(event: Dict, include_thinking: bool) -> Dict[str, Any]:
        """格式化更新事件（stream_mode="updates"）"""
        # event 格式: {"model": {"messages": [...]}} 或 {"tools": {"messages": [...]}}
        for node_name, node_output in event.items():
            if node_name in ("model", "agent"):
                # Agent/Model 节点输出，包含 messages
                messages = node_output.get("messages", []) if isinstance(node_output, dict) else []
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, 'type'):
                        if last_message.type == "ai":
                            content = getattr(last_message, 'content', "")
                            thinking_content = None
                            if include_thinking:
                                thinking_content = getattr(last_message, 'thinking_content', None)
                            return {
                                "type": "content",
                                "data": {"content": content, "thinking_content": thinking_content}
                            }
                        elif last_message.type == "tool":
                            return {
                                "type": "tool_call",
                                "data": {
                                    "name": getattr(last_message, 'name', None),
                                    "content": getattr(last_message, 'content', None)
                                }
                            }
            elif node_name == "tools":
                # 工具节点输出
                messages = node_output.get("messages", []) if isinstance(node_output, dict) else []
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, 'type') and last_message.type == "tool":
                        return {
                            "type": "tool_result",
                            "data": {
                                "name": getattr(last_message, 'name', None),
                                "content": getattr(last_message, 'content', None)
                            }
                        }
        return {"type": "unknown", "data": event}

    @staticmethod
    def _format_event(event: Dict, include_thinking: bool) -> Dict[str, Any]:
        """格式化Agent事件为前端可消费的格式"""
        messages = event.get("messages", [])
        if not messages:
            return {"type": "unknown", "data": event}

        last_message = messages[-1]

        # 处理 LangChain 消息对象（如 HumanMessage, AIMessage, ToolMessage）
        # 这些对象有 type 属性，而不是字典的 get 方法
        if hasattr(last_message, 'type'):
            message_type = last_message.type

            # 处理AI消息 (AIMessage)
            if message_type == "ai":
                content = last_message.content if hasattr(last_message, 'content') else ""

                # 检查是否有思考内容
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

            # 处理工具调用 (ToolMessage)
            elif message_type == "tool":
                return {
                    "type": "tool_call",
                    "data": {
                        "name": getattr(last_message, 'name', None),
                        "content": getattr(last_message, 'content', None)
                    }
                }

            # 处理人类消息 (HumanMessage) - 通常不需要返回给前端
            elif message_type == "human":
                return {"type": "human", "data": {"content": getattr(last_message, 'content', None)}}

        # 处理字典格式的消息（如果存在）
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
        # TODO: 实现文档内容提取
        return ""

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
        """使用Agent生成流式响应"""
        try:
            logger.info(f"[CHAT] 开始生成流式响应: conversation_id={conversation_id}")
            async for event in ChatService.process_message(
                conversation_id=conversation_id,
                content=content,
                images=images,
                is_expert=is_expert,
                enable_thinking=False
            ):
                if event["type"] == "token":
                    # 流式 token，直接输出
                    content = event["data"]["content"]
                    if content:
                        yield content
                elif event["type"] == "content":
                    # 完整内容（备用）
                    content = event["data"]["content"]
                    if content:
                        yield content
                elif event["type"] == "tool_call":
                    tool_name = event["data"].get("name", "unknown")
                    yield f"\n[使用工具: {tool_name}]\n"
                elif event["type"] == "tool_result":
                    # 工具执行结果，不显示给用户
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
                enable_thinking=False
            ):
                if event["type"] == "content":
                    full_response.append(event["data"]["content"])
                elif event["type"] == "tool_call":
                    full_response.append(f"\n[使用工具: {event['data']['name']}]\n")

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
            logger.info(f"[CACHE DELETE] 已删除消息缓存: conversation_id={conversation_id}, user_id={user_id}, keys={len(all_keys)}")
        else:
            logger.info(f"[CACHE DELETE] 未找到消息缓存: conversation_id={conversation_id}, user_id={user_id}")


chat_service = ChatService()
