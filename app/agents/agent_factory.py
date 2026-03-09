"""Agent工厂 - 使用 DeepAgents 的 create_deep_agent"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any

from langchain_community.chat_models import ChatTongyi
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.backends.filesystem import FilesystemBackend
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore

from app.config import settings
from app.tools.code_tools import code_assist
from app.tools.image_tools import generate_image, edit_image
from app.tools.multimodal_tool import understand_image
from app.tools.web_search_tool import web_search
from app.tools.rag_tool import search_knowledge_base
from app.tools.filesystem_tools import read_pdf, read_word

logger = logging.getLogger(__name__)


RESEARCHER_TOOLS = [web_search, search_knowledge_base, read_pdf, read_word]
CODER_TOOLS = [code_assist]
IMAGE_CREATOR_TOOLS = [generate_image, edit_image, understand_image]


SUBAGENTS = [
    {
        "name": "general-purpose",
        "description": "通用助手。用于搜索网络信息、执行多步骤任务。当需要联网搜索或处理通用任务时使用。",
        "system_prompt": """你是一个通用的AI助手，擅长搜索信息和执行多步骤任务。

你的任务是：
1. 使用 web_search 搜索网络信息
2. 综合整理信息，提供清晰的回答

输出要求：
- 信息准确
- 回答简洁明了""",
        "tools": [web_search],
    },
    {
        "name": "researcher",
        "description": "研究助手。用于深度研究、信息收集、知识检索。当用户需要研究某个主题、收集信息、分析文档时使用。",
        "system_prompt": """你是一个专业的研究助手，擅长信息收集和分析。

你的任务是：
1. 使用 web_search 搜索网络信息
2. 使用 search_knowledge_base 检索知识库
3. 使用 read_pdf / read_word 解析文档
4. 综合整理信息，提供结构化的研究报告

输出要求：
- 信息来源明确
- 观点有据可依
- 结构清晰有条理""",
        "tools": RESEARCHER_TOOLS,
    },
    {
        "name": "coder",
        "description": "代码助手。用于代码生成、代码解释、代码优化。当用户需要编程帮助时使用。",
        "system_prompt": """你是一个专业的编程助手，精通多种编程语言。

你的任务是：
1. 根据需求生成高质量代码
2. 解释代码逻辑和原理
3. 优化和重构代码
4. 解决编程问题

代码规范：
- 代码完整可运行
- 包含必要注释
- 遵循语言最佳实践
- 考虑边界情况和错误处理""",
        "tools": CODER_TOOLS,
    },
    {
        "name": "image-creator",
        "description": "图像创作助手。用于图像生成、图像编辑、图像理解。当用户需要创作或处理图像时使用。",
        "system_prompt": """你是一个专业的图像创作助手，擅长图像生成和编辑。

你的任务是：
1. 根据描述生成高质量图像
2. 编辑和优化现有图像
3. 分析和理解图像内容

创作原则：
- 提示词详细具体
- 考虑构图、色彩、风格
- 提供多种方案供选择""",
        "tools": IMAGE_CREATOR_TOOLS,
    },
]


SYSTEM_PROMPT = """你是一个任务分发助手，负责将用户请求分发给合适的子智能体处理。

## 记忆系统

你有以下记忆存储路径：

**长期记忆（跨会话持久化）**：
- `/memories/preferences.txt` - 用户偏好设置
- `/memories/knowledge/` - 知识库和笔记
- `/memories/instructions.txt` - 自改进指令

**会话记忆（摘要历史）**：
- `/conversation/` - 当前会话的摘要历史

**临时工作区（会话级）**：
- `/workspace/` - 临时文件和草稿

## 记忆使用规则

1. **用户偏好**：当用户表达偏好时，保存到 `/memories/preferences.txt`
2. **重要信息**：关键决策、项目信息等保存到 `/memories/knowledge/`
3. **自改进**：根据用户反馈更新 `/memories/instructions.txt`
4. **会话开始**：读取 `/memories/preferences.txt` 和 `/memories/instructions.txt`

## 技能使用规则

- 当用户请求匹配某个技能时，使用 read_file 读取技能文件
- 按照技能中的流程执行任务

对于简单的问候或闲聊，直接回复。
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
    """Agent工厂类 - Main Agent 只做任务分发"""

    _checkpointer: Optional[Union[AsyncPostgresSaver, InMemorySaver]] = None
    _context_manager: Optional[object] = None
    _initialized: bool = False
    _agent_cache: Dict[str, Any] = {}
    _skills_backend: Optional[FilesystemBackend] = None
    _store: Optional[BaseStore] = None
    _store_context: Optional[object] = None

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
    async def init_store(cls) -> bool:
        """初始化长期记忆存储 (BaseStore)
        
        用于 StoreBackend 持久化跨线程记忆。
        
        Returns:
            bool: 是否成功使用 PostgreSQL
        """
        try:
            if settings.database_url:
                from langgraph.store.postgres import PostgresStore
                cls._store_context = PostgresStore.from_conn_string(settings.database_url)
                cls._store = cls._store_context.__enter__()
                cls._store.setup()
                logger.info("[AGENT] PostgresStore initialized for long-term memory")
                return True
        except Exception as e:
            logger.warning(f"[AGENT] PostgresStore init failed, fallback to InMemoryStore: {e}")
        
        cls._store = InMemoryStore()
        cls._store_context = None
        return False

    @classmethod
    async def close_store(cls) -> None:
        """关闭长期记忆存储"""
        if cls._store_context and hasattr(cls._store_context, '__exit__'):
            try:
                cls._store_context.__exit__(None, None, None)
                logger.info("[AGENT] PostgresStore connection closed")
            except Exception as e:
                logger.error(f"[AGENT] Failed to close PostgresStore: {e}")
        cls._store = None
        cls._store_context = None

    @classmethod
    def get_store(cls) -> BaseStore:
        """获取长期记忆存储实例
        
        Returns:
            BaseStore 实例
        """
        if cls._store is None:
            raise RuntimeError("Store not initialized. Call init_store() first.")
        return cls._store

    @classmethod
    def _make_backend(cls, runtime) -> CompositeBackend:
        """创建复合后端 - 路由持久化路径到 StoreBackend
        
        路径规划：
        - /memories/     → StoreBackend (跨会话持久化)
        - /conversation/ → StoreBackend (会话摘要历史)
        - /skills/       → FilesystemBackend (本地技能文件)
        - 其他           → StateBackend (临时存储)
        """
        def get_user_id(ctx) -> str:
            context = ctx.runtime.context
            if context is None:
                return "default"
            return str(context.get("user_id", "default"))
        
        def get_thread_id(ctx) -> str:
            context = ctx.runtime.context
            if context is None:
                return "default"
            return str(context.get("thread_id", "default"))
        
        memories_backend = StoreBackend(
            runtime,
            namespace=lambda ctx: (
                get_user_id(ctx),
                "memories"
            )
        )
        
        conversation_backend = StoreBackend(
            runtime,
            namespace=lambda ctx: (
                get_user_id(ctx),
                "conversations",
                get_thread_id(ctx)
            )
        )
        
        skills_backend = cls._get_skills_backend()
        
        return CompositeBackend(
            default=StateBackend(runtime),
            routes={
                "/memories/": memories_backend,
                "/conversation/": conversation_backend,
                "/skills/": skills_backend,
            }
        )

    @classmethod
    def _get_skills_backend(cls) -> FilesystemBackend:
        """获取文件系统后端（用于技能文件）
        
        注意：CompositeBackend 会剥离路由前缀，所以 root_dir 应该是 skills 目录本身。
        例如：/skills/my_skill/SKILL.md → 剥离前缀后 → /my_skill/SKILL.md
        FilesystemBackend 的 root_dir 应该是 skills 目录，这样解析后就是正确的路径。
        
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
            
            # root_dir 应该是 skills 目录，因为 CompositeBackend 会剥离 /skills/ 前缀
            cls._skills_backend = FilesystemBackend(
                root_dir=skills_dir,
                virtual_mode=True,
            )
            logger.debug(f"[AGENT] Initialized skills backend: {skills_dir}")
        return cls._skills_backend

    @classmethod
    def create_chat_agent(
        cls,
        is_expert: bool = False,
        enable_thinking: bool = False
    ):
        """创建聊天Agent (使用 DeepAgents 的 create_deep_agent)

        Main Agent 只做任务分发，不传入业务工具。
        所有业务任务委托给子智能体处理。
        
        内置能力:
        - TodoListMiddleware: 任务规划工具 (write_todos)
        - FilesystemMiddleware: 文件系统工具 (read_file, write_file, edit_file 等)
        - SubAgentMiddleware: 子智能体委托 (task)
        - SummarizationMiddleware: 自动上下文摘要
        - SkillsMiddleware: 技能加载 (通过 skills 参数配置)
        - 长期记忆: 通过 CompositeBackend 路由 /memories/ 到 StoreBackend

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
        store = cls.get_store()
        
        agent = create_deep_agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=checkpointer,
            store=store,
            backend=cls._make_backend,
            skills=["/skills/"],
            subagents=SUBAGENTS,
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
    def get_agent_config(cls, conversation_id: str, user_id: Optional[int] = None) -> dict:
        """获取Agent配置 - 用于区分不同对话线程
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于长期记忆命名空间隔离）
            
        Returns:
            配置字典，包含 thread_id、user_id 和 recursion_limit
        """
        config = {
            "configurable": {
                "thread_id": f"conversation_{conversation_id}"
            },
            "recursion_limit": settings.agent_recursion_limit
        }
        
        if user_id is not None:
            config["context"] = {
                "user_id": user_id,
                "thread_id": conversation_id
            }
        
        return config

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
