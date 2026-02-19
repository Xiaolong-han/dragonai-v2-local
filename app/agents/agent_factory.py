"""Agent工厂 - 使用LangChain 1.0+推荐的create_agent"""

import asyncio
import os
from typing import Optional
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from app.config import settings
from app.tools import ALL_TOOLS
from app.llm.model_factory import ModelFactory


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
`````

请根据用户的需求，合理选择和使用这些工具。如果用户请求不明确，请主动询问以澄清需求。
"""


class AgentFactory:
    """Agent工厂类 - 使用LangChain 1.0+推荐的create_agent"""

    _checkpointer: Optional[InMemorySaver] = None

    @classmethod
    def get_checkpointer(cls) -> InMemorySaver:
        """获取InMemorySaver实例

        使用内存存储作为checkpointer
        注意：重启后对话状态会丢失，如需持久化请使用PostgresSaver（非Windows环境）
        """
        if cls._checkpointer is None:
            cls._checkpointer = InMemorySaver()
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
        # 1. 获取模型
        model = ModelFactory.get_general_model(
            is_expert=is_expert,
            thinking=enable_thinking
        )

        # 2. 获取checkpointer用于对话状态持久化
        checkpointer = cls.get_checkpointer()

        # 3. 创建Agent (LangChain 1.0+ 推荐方式)
        # 直接传递工具列表，无需ToolRegistry
        # 传入checkpointer实现对话状态持久化
        # 参考: https://python.langchain.com/docs/how_to/agent/
        agent = create_agent(
            model=model,
            tools=ALL_TOOLS,  # 直接传递工具列表
            system_prompt=SYSTEM_PROMPT,
            checkpointer=checkpointer,  # 传入InMemorySaver
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
