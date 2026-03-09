import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, Optional, List

from app.services.formatters.message_formatter import MessageFormatter
from app.agents.error_classifier import AgentErrorClassifier, AgentErrorType
from app.config import settings

logger = logging.getLogger(__name__)


class StreamProcessor:
    """流式处理器，负责处理 Agent 流式输出"""
    
    def __init__(self, formatter: Optional[MessageFormatter] = None):
        self.formatter = formatter or MessageFormatter()
    
    async def process_agent_stream(
        self,
        agent,
        config: Dict,
        full_context: str,
        enable_thinking: bool
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """统一的 Agent 流处理逻辑"""
        tool_call_count = 0
        
        async for stream_mode, data in agent.astream(
            {"messages": [{"role": "user", "content": full_context}]},
            config,
            stream_mode=["messages", "updates"]
        ):
            if stream_mode == "messages":
                message, metadata = data
                formatted = self.formatter.format_stream_message(message, metadata, enable_thinking)
                if formatted:
                    yield formatted
            elif stream_mode == "updates":
                for source, update in data.items():
                    if source in ("model", "tools"):
                        formatted_list = self.formatter.format_update({source: update}, enable_thinking)
                        for formatted in formatted_list:
                            if formatted.get("type") == "tool_call":
                                tool_call_count += 1
                                if tool_call_count > settings.agent_tool_call_limit:
                                    logger.error(f"[STREAM] 工具调用超过限制: {tool_call_count} > {settings.agent_tool_call_limit}")
                                    return
                            if formatted.get("type") not in ("unknown", None):
                                yield formatted
    
    async def process_message(
        self,
        conversation_id: int,
        content: str,
        user_id: Optional[int] = None,
        attachments: Optional[List[str]] = None,
        is_expert: bool = False,
        enable_thinking: bool = False,
        agent_factory=None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理用户消息 - 支持多模态输入和Agent工具调用
        
        Args:
            conversation_id: 对话ID
            content: 用户消息内容
            user_id: 用户ID（用于长期记忆命名空间隔离）
            attachments: 附件列表
            is_expert: 是否使用专家模型
            enable_thinking: 是否启用深度思考
            agent_factory: Agent工厂实例
        """
        try:
            logger.info(f"[STREAM] 开始处理消息: conversation_id={conversation_id}")

            full_context = self._build_context(content, attachments)
            logger.debug(f"[STREAM] 上下文准备完成，长度: {len(full_context)}")

            if agent_factory is None:
                from app.agents.agent_factory import AgentFactory
                agent_factory = AgentFactory
            
            agent = agent_factory.create_chat_agent(
                is_expert=is_expert,
                enable_thinking=enable_thinking
            )
            config = agent_factory.get_agent_config(str(conversation_id), user_id=user_id)

            logger.debug(f"[STREAM] 开始流式执行Agent")
            
            try:
                async with asyncio.timeout(settings.agent_timeout):
                    async for event in self.process_agent_stream(
                        agent, config, full_context, enable_thinking
                    ):
                        yield event
            except asyncio.TimeoutError:
                logger.error(f"[STREAM] Agent执行超时，conversation_id={conversation_id}")
                yield {"type": "error", "data": {"message": "请求处理超时，请稍后重试"}}
                return

            logger.info(f"[STREAM] Agent流式执行完成")
            
        except Exception as e:
            error_type = AgentErrorClassifier.classify(e)
            logger.error(f"[STREAM] 处理消息时出错: type={error_type.value}, error={str(e)}", exc_info=True)
            
            if AgentErrorClassifier.is_retryable(error_type):
                async for event in self._retry_on_tool_call_error(
                    conversation_id, full_context, is_expert, enable_thinking, user_id, agent_factory
                ):
                    yield event
            else:
                user_message = AgentErrorClassifier.get_user_message(
                    error_type, 
                    is_production=(settings.app_env == "production")
                )
                yield {"type": "error", "data": {"message": user_message}}
    
    def _build_context(self, content: str, attachments: Optional[List[str]]) -> str:
        """构建消息上下文"""
        context_parts = [content]

        if attachments:
            for attachment in attachments:
                context_parts.append(f"[附件路径: {attachment}]")

        return "\n\n".join(context_parts)
    
    async def _retry_on_tool_call_error(
        self,
        conversation_id: int,
        full_context: str,
        is_expert: bool,
        enable_thinking: bool,
        user_id: Optional[int] = None,
        agent_factory=None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理 tool_calls 错误并重试"""
        logger.warning(f"[STREAM] 检测到无效的tool_calls，清理对话状态并重试")
        
        if agent_factory is None:
            from app.agents.agent_factory import AgentFactory
            agent_factory = AgentFactory
        
        await agent_factory.reset_conversation_state(str(conversation_id))
        
        try:
            agent = agent_factory.create_chat_agent(
                is_expert=is_expert,
                enable_thinking=enable_thinking
            )
            config = agent_factory.get_agent_config(str(conversation_id), user_id=user_id)
            
            async with asyncio.timeout(settings.agent_timeout):
                async for event in self.process_agent_stream(
                    agent, config, full_context, enable_thinking
                ):
                    yield event
            logger.info(f"[STREAM] 重试执行成功")
            
        except asyncio.TimeoutError:
            logger.error(f"[STREAM] 重试执行超时，conversation_id={conversation_id}")
            yield {"type": "error", "data": {"message": AgentErrorClassifier.get_user_message(AgentErrorType.TIMEOUT)}}
        except Exception as retry_error:
            error_type = AgentErrorClassifier.classify(retry_error)
            logger.error(f"[STREAM] 重试执行失败: type={error_type.value}, error={str(retry_error)}")
            user_message = AgentErrorClassifier.get_user_message(
                error_type,
                is_production=(settings.app_env == "production")
            )
            yield {"type": "error", "data": {"message": user_message}}
