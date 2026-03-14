"""Agent工厂 - 使用LangChain Deep Agent"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any

from langchain.agents import create_agent
from langchain.agents.middleware import (
    SummarizationMiddleware,
    ContextEditingMiddleware,
    ClearToolUsesEdit,
    LLMToolSelectorMiddleware,
    ToolCallLimitMiddleware,
    ToolRetryMiddleware,
    ModelCallLimitMiddleware,
    ModelFallbackMiddleware,
)
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from deepagents.middleware.skills import SkillsMiddleware
from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware
from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.backends import CompositeBackend, StateBackend

from app.config import settings
from app.llm.model_factory import ModelFactory
from app.agents.backends import BackendManager

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

**文件系统路径规则（非常重要）**：
你有一个虚拟文件系统，不同路径有不同的用途和持久化策略：

1. **临时文件 `/`** (默认路径)
   - 用途：存放临时生成的文件、代码、数据
   - 持久化：仅当前会话有效，会话结束后自动清除
   - 示例：`/temp.py`, `/analysis_result.json`

2. **技能文件 `/skills/`** (只读)
   - 用途：存放预定义的技能文件(SKILL)，包含特定任务的执行流程
   - 持久化：存储在本地文件系统，跨会话持久
   - 访问：只读，不要尝试写入
   - 示例：`/skills/web_search.md`, `/skills/code_review.md`

3. **长期记忆 `/memories/`** (读写，用户隔离)
   - 用途：存放需要跨会话保留的用户特定信息，如用户画像、偏好设置、学习记录
   - 持久化：存储在 PostgreSQL 数据库，按用户ID隔离，永久保留
   - 隔离机制：每个用户的记忆存储在独立的 namespace 中
   - 使用场景：
     * 用户说"记住我喜欢Python" -> 写入 `/memories/user_profile.md`
     * 用户纠正你的错误 -> 记录到 `/memories/lessons.md`
     * 需要记住的配置信息 -> 保存到 `/memories/config.md`
   - 示例：`/memories/user_profile.md`, `/memories/preferences.json`
   - **注意**：用户只能访问自己的 `/memories/`，无法看到其他用户的记忆

**记忆管理最佳实践**：
- 主动记录用户偏好和重要信息到 `/memories/`
- 使用结构化格式（如 Markdown、JSON）便于后续读取
- 定期整理记忆文件，避免信息过于分散

请根据用户的需求，合理选择和使用工具。如果用户请求不明确，请主动询问以澄清需求。
"""


class AgentFactory:
    """Agent工厂类 - 使用LangChain 1.0+推荐的create_agent"""

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
    async def init_backends(cls) -> bool:
        """初始化所有后端 (checkpointer + store + composite)"""
        # 初始化 checkpointer (原有逻辑)
        checkpointer_result = await cls.init_checkpointer()

        # 初始化 composite backend (包含 PostgresStore)
        store_result = await BackendManager.initialize()

        return checkpointer_result and store_result

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
        logger.info("[AGENT] Cache cleared")

    @classmethod
    async def close_backends(cls) -> None:
        """关闭所有后端连接"""
        await cls.close_checkpointer()  # 原有逻辑
        await BackendManager.close()     # 关闭 PostgresStore 等

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
        """获取技能文件系统后端
        
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
        """创建聊天Agent (LangChain 1.0+ 推荐方式)

        使用create_agent创建ReAct模式的Agent，无需AgentExecutor。
        内部基于LangGraph构建，支持持久化、流式输出等特性。
        
        使用缓存机制，相同配置的agent只创建一次，通过thread_id区分不同对话。
        
        集成中间件: SkillsMiddleware, PatchToolCallsMiddleware, 
        LLMToolSelectorMiddleware, ContextEditingMiddleware, 
        SummarizationMiddleware, ToolCallLimitMiddleware,
        ModelCallLimitMiddleware, ToolRetryMiddleware, ModelFallbackMiddleware

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
        
        main_model = ModelFactory.get_general_model(
            is_expert=is_expert,
            enable_thinking=enable_thinking
        )
        
        middleware = cls._build_middleware()
        
        # 获取 store，如果 BackendManager 未初始化则使用 None
        try:
            store = BackendManager.get_store()
        except RuntimeError:
            store = None

        # 延迟导入避免循环导入
        from app.tools import ALL_TOOLS

        agent = create_agent(
            model=main_model,
            tools=ALL_TOOLS,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=cls.get_checkpointer(),
            store=store,  # 传入 PostgresStore 用于长期记忆
            middleware=middleware,
        )
        
        cls._agent_cache[cache_key] = agent
        logger.debug(f"[AGENT] Created and cached agent: {cache_key}")

        return agent
    
    @classmethod
    def _build_middleware(cls) -> list:
        """构建Agent中间件列表"""
        fallback_model = ModelFactory.get_general_model(is_expert=False, enable_thinking=False)
        summary_model = ModelFactory.get_general_model(is_expert=False, enable_thinking=False, streaming=False)

        try:
            composite_factory = BackendManager.get_composite_factory()
        except RuntimeError:
            storage_dir = Path(settings.storage_dir).resolve()
            if not storage_dir.exists():
                storage_dir.mkdir(parents=True, exist_ok=True)
            skills_dir = storage_dir / "skills"
            if not skills_dir.exists():
                skills_dir.mkdir(parents=True, exist_ok=True)
            fallback_filesystem = FilesystemBackend(root_dir=storage_dir, virtual_mode=True)
            composite_factory = lambda rt: CompositeBackend(
                default=StateBackend(rt),
                routes={"/skills/": fallback_filesystem}
            )

        return [
            FilesystemMiddleware(backend=composite_factory),
            SkillsMiddleware(backend=composite_factory, sources=["/skills/"]),
            PatchToolCallsMiddleware(),
            SummarizationMiddleware(model=summary_model, max_tokens_before_summary=8000, messages_to_keep=6),
            ToolCallLimitMiddleware(run_limit=settings.agent_tool_call_limit, exit_behavior="end"),
            ModelCallLimitMiddleware(run_limit=50, exit_behavior="end"),
            ToolRetryMiddleware(max_retries=3, backoff_factor=2.0),
            ModelFallbackMiddleware(fallback_model),
        ]

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
    def get_agent_config(cls, conversation_id: str, user_id: int | None = None) -> dict:
        """获取Agent配置 - 用于区分不同对话线程

        Args:
            conversation_id: 对话ID
            user_id: 用户ID，用于长期记忆的 namespace 隔离

        Returns:
            配置字典，包含 thread_id、recursion_limit 和 user_id
        """
        config = {
            "configurable": {
                "thread_id": f"conversation_{conversation_id}"
            },
            "recursion_limit": settings.agent_recursion_limit
        }

        # 添加 user_id 到 context，用于 StoreBackend 的 namespace
        if user_id is not None:
            config["context"] = {"user_id": user_id}

        return config

