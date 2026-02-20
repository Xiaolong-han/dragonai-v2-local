"""Agent工厂 - 使用LangChain 1.0+推荐的create_agent"""

import logging
from typing import Optional, Union

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.config import settings
from app.tools import ALL_TOOLS
from app.llm.model_factory import ModelFactory

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是一个强大的AI助手，能够帮助用户处理各种任务。

你可以使用以下工具来帮助用户：

1. **search_knowledge_base** - 从本地知识库搜索信息
   - 当用户询问项目文档、技术规范、内部资料时使用

2. **web_search** - 联网搜索最新信息
   - 当用户询问新闻、实时信息、公开资料时使用

3. **ocr_document** - 识别图片中的文字
   - 当用户上传包含文字的图片时使用

4. **understand_image** - 理解图片内容
   - 当用户上传图片并询问图片内容时使用

5. **generate_image** - 生成图像
   - 当用户要求生成、绘制、创建图像时使用

6. **edit_image** - 编辑图像
   - 当用户要求修改、编辑已有图像时使用

7. **code_assist** - 编程协助
   - 当用户需要写代码、调试代码、解释代码时使用

8. **translate_text** - 翻译文本
   - 当用户需要翻译内容时使用

**重要规则**：
- 当工具返回内容时，你应该将工具返回的内容完整地展示给用户
- 特别是 当使用 code_assist 工具返回的代码时，你必须在最终回复中完整展示生成的代码块。禁止仅提供代码的摘要或描述。
- 请使用标准Markdown格式包裹代码块，例如：````
```python
print("Hello, World!")
```
````

请根据用户的需求，合理选择和使用这些工具。如果用户请求不明确，请主动询问以澄清需求。
"""


class AgentFactory:
    """Agent工厂类 - 使用LangChain 1.0+推荐的create_agent"""

    _checkpointer: Optional[Union[AsyncPostgresSaver, InMemorySaver]] = None
    _context_manager: Optional[object] = None
    _initialized: bool = False

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
                logger.info("[AGENT] AsyncPostgresSaver 初始化成功")
                return True
        except Exception as e:
            logger.warning(f"[AGENT] AsyncPostgresSaver 初始化失败，降级使用 InMemorySaver: {e}")
        
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
                logger.info("[AGENT] AsyncPostgresSaver 连接已关闭")
            except Exception as e:
                logger.error(f"[AGENT] 关闭 AsyncPostgresSaver 连接失败: {e}")
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
    def create_chat_agent(
        cls,
        is_expert: bool = False,
        enable_thinking: bool = False
    ):
        """创建聊天Agent (LangChain 1.0+ 推荐方式)

        使用create_agent创建ReAct模式的Agent，无需AgentExecutor。
        内部基于LangGraph构建，支持持久化、流式输出等特性。

        Args:
            is_expert: 是否使用专家模型
            enable_thinking: 是否启用深度思考

        Returns:
            Agent实例，可直接调用invoke或stream
        """
        model = ModelFactory.get_general_model(
            is_expert=is_expert,
            thinking=enable_thinking
        )

        checkpointer = cls.get_checkpointer()

        agent = create_agent(
            model=model,
            tools=ALL_TOOLS,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=checkpointer,
        )

        return agent

    @classmethod
    def get_agent_config(cls, conversation_id: str) -> dict:
        """获取Agent配置 - 用于区分不同对话线程"""
        return {
            "configurable": {
                "thread_id": f"conversation_{conversation_id}"
            }
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
