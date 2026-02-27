"""Agent工厂 - 使用LangChain Deep Agent"""

import logging
from pathlib import Path
from typing import Optional, Union

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from deepagents.middleware.skills import SkillsMiddleware
from deepagents.backends.filesystem import FilesystemBackend

from app.config import settings
from app.tools import ALL_TOOLS
from app.llm.model_factory import ModelFactory

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是一个强大的AI助手，能够帮助用户处理各种任务。

你可以使用多种工具来帮助用户，工具的功能说明已内置在系统中。

**工具调用重要规则**：
- 如果调用工具缺少必填参数，不要调用工具，应该先询问用户提供缺失的信息
- 根据用户需求选择最合适的工具，避免不必要的工具调用

**工具结果输出规则（非常重要）**：
- 当工具返回结果包含代码、完整答案或详细内容时，你必须原样完整输出给用户
- 禁止对工具返回的代码进行总结、省略、改写或简化
- 禁止使用"代码如下"、"这是代码"等简短描述代替完整输出
- 如果工具结果包含<INSTRUCTION>标签，必须严格遵循标签内的指令
- 当看到<INSTRUCTION>标签时，只输出标签后的内容，不要输出标签本身，不要做任何修改

**技能使用规则（非常重要）**：
- 当用户请求匹配某个技能的描述时，你必须先调用 read_file 读取该技能的完整指令
- 禁止在没有读取技能文件的情况下直接回答相关任务
- 读取技能文件后，必须严格按照技能中的流程和模板执行任务

**文件系统工具使用说明**：
- ls: 列出目录内容，- read_file: 读取文件内容（支持文本和图片）
- write_file: 创建新文件
- edit_file: 编辑现有文件
- glob: 按模式搜索文件
- grep: 在文件中搜索文本
- read_pdf: 读取PDF文件
- read_word: 读取Word文档

请根据用户的需求，合理选择和使用工具。如果用户请求不明确，请主动询问以澄清需求。
"""


class AgentFactory:
    """Agent工厂类 - 使用LangChain 1.0+推荐的create_agent"""

    _checkpointer: Optional[Union[AsyncPostgresSaver, InMemorySaver]] = None
    _context_manager: Optional[object] = None
    _initialized: bool = False
    _agent_cache: dict = {}
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
        
        在应用关闭时调用，清理数据库连接。
        """
        if cls._context_manager and hasattr(cls._context_manager, '__aexit__'):
            try:
                await cls._context_manager.__aexit__(None, None, None)
                logger.info("[AGENT] AsyncPostgresSaver connection closed")
            except Exception as e:
                logger.error(f"[AGENT] Failed to close AsyncPostgresSaver connection: {e}")
        cls._checkpointer = None
        cls._context_manager = None

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
            skills_dir = Path(settings.skills_dir).resolve()
            if not skills_dir.exists():
                skills_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"[AGENT] Created skills directory: {skills_dir}")
            
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
        """创建聊天Agent (LangChain 1.0+ 推荐方式)

        使用create_agent创建ReAct模式的Agent，无需AgentExecutor。
        内部基于LangGraph构建，支持持久化、流式输出等特性。
        
        使用缓存机制，相同配置的agent只创建一次，通过thread_id区分不同对话。
        
        集成 Skills:
        - SkillsMiddleware: 扫描技能目录，注入技能列表到系统提示

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
        
        model = ModelFactory.get_general_model(
            is_expert=is_expert,
            thinking=enable_thinking
        )

        checkpointer = cls.get_checkpointer()
        
        skills_backend = cls._get_skills_backend()
        
        middleware = [
            SkillsMiddleware(backend=skills_backend, sources=["/"]),
        ]

        agent = create_agent(
            model=model,
            tools=ALL_TOOLS,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=checkpointer,
            middleware=middleware,
        )
        
        cls._agent_cache[cache_key] = agent
        logger.debug(f"[AGENT] Created and cached agent: {cache_key}")

        return agent

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
