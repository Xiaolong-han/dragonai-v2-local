"""Agent工厂 - 使用 DeepAgents 的 create_deep_agent"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any

from langchain_community.chat_models import ChatTongyi
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend

from app.config import settings
from app.tools import ALL_TOOLS

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是一个强大的AI助手，能够帮助用户处理各种任务。

你可以使用多种工具来帮助用户，工具的功能说明已内置在系统中。

**工具调用重要规则**：
- 如果调用工具缺少必填参数，不要调用工具，应该先询问用户提供缺失的信息
- 根据用户需求选择最合适的工具，避免不必要的工具调用

**技能使用规则（非常重要）**：
- 当用户请求匹配某个技能的描述时，你必须先调用 read_file 读取该技能的完整SKILL文件
- 禁止在没有读取技能文件的情况下直接回答相关任务
- 读取技能文件后，必须严格按照技能中的流程和模板执行任务

请根据用户的需求，合理选择和使用工具。如果用户请求不明确，请主动询问以澄清需求。
"""


_chat_model_cache: Dict[str, ChatTongyi] = {}


def get_chat_model(
    is_expert: bool = False,
    enable_thinking: bool = False,
    use_cache: bool = True,
) -> ChatTongyi:
    """获取聊天模型（连接池复用）

    使用 LangChain 的 ChatTongyi 创建模型，支持 bind_tools (用于 Agent)

    Args:
        is_expert: 是否使用专家模型
        enable_thinking: 是否启用深度思考
        use_cache: 是否使用缓存（默认True）
    """
    cache_key = f"chat_{is_expert}_{enable_thinking}"

    if use_cache and cache_key in _chat_model_cache:
        logger.debug(f"[AGENT] ChatTongyi cache hit: {cache_key}")
        return _chat_model_cache[cache_key]

    model_name = (
        settings.model_general_expert if is_expert
        else settings.model_general_fast
    )

    model_kwargs = {}
    if enable_thinking:
        model_kwargs["enable_thinking"] = True
        model_kwargs["incremental_output"] = True
    else:
        model_kwargs["enable_thinking"] = False
        model_kwargs["incremental_output"] = True

    client = ChatTongyi(
        model=model_name,
        dashscope_api_key=settings.qwen_api_key,
        streaming=True,
        temperature=0.3 if enable_thinking else 0.6,
        model_kwargs=model_kwargs if model_kwargs else None,
        request_timeout=60,
        max_retries=3
    )

    if use_cache:
        _chat_model_cache[cache_key] = client
        logger.debug(f"[AGENT] ChatTongyi created and cached: {cache_key}")

    return client


class AgentFactory:
    """Agent工厂类 - 使用 DeepAgents 的 create_deep_agent"""

    _checkpointer: Optional[Union[AsyncPostgresSaver, InMemorySaver]] = None
    _context_manager: Optional[object] = None
    _initialized: bool = False
    _agent_cache: Dict[str, Any] = {}
    _skills_backend: Optional[FilesystemBackend] = None

    @classmethod
    async def init_checkpointer(cls) -> bool:
        """初始化 checkpointer (异步版本)
        
        在应用启动时调用，创建数据库连接并初始化表结构。
        
        Returns:
            bool: 是否成功使用 PostgreSQL
        """
        try:
            if settings.database_url:
                cls._context_manager = AsyncPostgresSaver.from_conn_string(settings.database_url)
                cls._checkpointer = await cls._context_manager.__aenter__()
                if not cls._initialized:
                    await cls._checkpointer.setup()
                    cls._initialized = True
                logger.info("[AGENT] AsyncPostgresSaver initialized")
                return True
        except Exception as e:
            logger.warning(f"[AGENT] AsyncPostgresSaver init failed, fallback to InMemorySaver: {e}")
        
        cls._checkpointer = InMemorySaver()
        cls._context_manager = None
        return False

    @classmethod
    async def close_checkpointer(cls) -> None:
        """关闭 checkpointer 连接 (异步版本)
        
        在应用关闭时调用，清理数据库连接和缓存。
        """
        if cls._context_manager and hasattr(cls._context_manager, '__aexit__'):
            try:
                await cls._context_manager.__aexit__(None, None, None)
                logger.info("[AGENT] AsyncPostgresSaver connection closed")
            except Exception as e:
                logger.error(f"[AGENT] Failed to close AsyncPostgresSaver connection: {e}")
        cls._checkpointer = None
        cls._context_manager = None
        cls._agent_cache.clear()
        cls._skills_backend = None
        _chat_model_cache.clear()
        logger.info("[AGENT] Cache cleared")

    @classmethod
    def get_checkpointer(cls) -> Union[AsyncPostgresSaver, InMemorySaver]:
        """获取 checkpointer 实例
        
        如果尚未初始化，会自动初始化。
        
        Returns:
            AsyncPostgresSaver 或 InMemorySaver 实例
        """
        if cls._checkpointer is None:
            raise RuntimeError("Checkpointer not initialized. Call init_checkpointer() first.")
        return cls._checkpointer

    @classmethod
    def _get_skills_backend(cls) -> FilesystemBackend:
        """获取文件系统后端（用于 create_deep_agent 的 backend 参数）
        
        后端的 root_dir 配置了存储目录，技能文件存放在 {root_dir}/skills/ 目录下。
        create_deep_agent 的 skills 参数指定的路径相对于此 root_dir。
        
        Returns:
            FilesystemBackend 实例
        """
        if cls._skills_backend is None:
            storage_dir = Path(settings.storage_dir).resolve()
            if not storage_dir.exists():
                storage_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"[AGENT] Created storage directory: {storage_dir}")
            
            skills_dir = storage_dir / "skills"
            if not skills_dir.exists():
                skills_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"[AGENT] Created skills directory: {skills_dir}")
            
            cls._skills_backend = FilesystemBackend(
                root_dir=storage_dir,
                virtual_mode=True,
            )
            logger.debug(f"[AGENT] Initialized skills backend: {storage_dir}")
        return cls._skills_backend

    @classmethod
    def create_chat_agent(
        cls,
        is_expert: bool = False,
        enable_thinking: bool = False
    ):
        """创建聊天Agent (使用 DeepAgents 的 create_deep_agent)

        使用 create_deep_agent 创建深度智能体，内置任务规划、文件系统、子智能体等能力。
        内部基于 LangGraph 构建，支持持久化、流式输出等特性。
        
        使用缓存机制，相同配置的agent只创建一次，通过thread_id区分不同对话。
        
        内置能力:
        - TodoListMiddleware: 任务规划工具 (write_todos)
        - FilesystemMiddleware: 文件系统工具 (read_file, write_file, edit_file 等)
        - SubAgentMiddleware: 子智能体委托 (task)
        - SummarizationMiddleware: 自动上下文摘要
        - SkillsMiddleware: 技能加载 (通过 skills 参数配置)

        Args:
            is_expert: 是否使用专家模型
            enable_thinking: 是否启用深度思考

        Returns:
            Agent实例，可直接调用invoke或stream
        """
        cache_key = f"expert_{is_expert}_thinking_{enable_thinking}"
        
        if cache_key in cls._agent_cache:
            logger.debug(f"[AGENT] Using cached agent: {cache_key}")
            return cls._agent_cache[cache_key]
        
        model = get_chat_model(
            is_expert=is_expert,
            enable_thinking=enable_thinking
        )

        checkpointer = cls.get_checkpointer()
        
        backend = cls._get_skills_backend()

        agent = create_deep_agent(
            model=model,
            tools=ALL_TOOLS,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=checkpointer,
            backend=backend,
            skills=["/skills/"],
        )
        
        cls._agent_cache[cache_key] = agent
        logger.debug(f"[AGENT] Created and cached agent: {cache_key}")

        return agent

    @classmethod
    async def warmup(cls):
        """启动预热：并发创建全部 4 种配置
        
        在应用启动时调用，避免首次请求延迟。
        使用 asyncio.gather 并发创建，减少启动时间。
        """
        configs = [
            (False, False),
            (True, False),
            (False, True),
            (True, True),
        ]

        logger.info("[AGENT] Starting concurrent warmup...")
        
        async def create_agent_safe(is_expert: bool, thinking: bool) -> Optional[str]:
            """安全创建 Agent，返回缓存键或 None"""
            try:
                cls.create_chat_agent(is_expert, thinking)
                return f"expert_{is_expert}_thinking_{thinking}"
            except Exception as e:
                logger.warning(f"[AGENT] Warmup failed for expert={is_expert}, thinking={thinking}: {e}")
                return None
        
        results = await asyncio.gather(
            *[create_agent_safe(is_expert, thinking) for is_expert, thinking in configs]
        )
        
        successful = [r for r in results if r is not None]
        logger.info(f"[AGENT] Warmup completed, cached: {len(successful)}/{len(configs)}")

    @classmethod
    def get_cache_stats(cls) -> dict:
        """获取缓存状态
        
        Returns:
            包含缓存信息的字典
        """
        return {
            "cached_agents": list(cls._agent_cache.keys()),
            "total": len(cls._agent_cache),
            "max": 4,
        }

    @classmethod
    def get_agent_config(cls, conversation_id: str) -> dict:
        """获取Agent配置 - 用于区分不同对话线程
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            配置字典，包含 thread_id 和 recursion_limit
        """
        return {
            "configurable": {
                "thread_id": f"conversation_{conversation_id}"
            },
            "recursion_limit": settings.agent_recursion_limit
        }

    @classmethod
    async def reset_conversation_state(cls, conversation_id: str) -> bool:
        """重置对话状态 (异步版本)
        
        清理指定对话的checkpointer状态，用于处理无效的tool_calls等问题。
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            是否成功清理
        """
        try:
            checkpointer = cls.get_checkpointer()
            thread_id = f"conversation_{conversation_id}"
            
            if hasattr(checkpointer, 'adelete_thread'):
                await checkpointer.adelete_thread(thread_id)
                return True
            elif hasattr(checkpointer, 'delete_thread'):
                checkpointer.delete_thread(thread_id)
                return True
            elif hasattr(checkpointer, '_storage'):
                if thread_id in checkpointer._storage:
                    del checkpointer._storage[thread_id]
                    return True
            return False
        except Exception as e:
            logger.error(f"[AGENT] 重置对话状态失败: {e}")
            return False
