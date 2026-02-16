
from typing import Optional
from enum import Enum

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

from app.llm import LangChainQwenChatModel
from app.tools import (
    search_knowledge_base,
    web_search,
    ocr_document,
    understand_image,
)
from app.skills.middleware import SkillMiddleware
from app.skills.loader_tool import load_skill
from app.storage.agent_saver import agent_saver_manager


class AgentType(Enum):
    GENERAL = "general"
    CODE = "code"
    TRANSLATION = "translation"
    IMAGE = "image"


SYSTEM_PROMPT = """你是一个强大的AI助手，能够帮助用户处理各种任务。

你拥有以下能力：
1. 知识库检索 - 可以从本地知识库中查找相关信息
2. 联网搜索 - 可以搜索互联网获取最新信息
3. 多模态处理 - 可以理解和分析图片内容，进行OCR文字识别
4. 专项技能 - 可以加载和使用各种专项技能（如图像生成、编程、翻译等）

请根据用户的需求，合理选择和使用这些能力，为用户提供最好的帮助。
"""


def create_general_agent(
    model_name: str = "qwen-flash",
    temperature: float = 0.7,
    thinking: bool = False,
    use_postgres_saver: bool = True,
):
    """创建通用聊天Agent
    
    Args:
        model_name: 使用的模型名称 (qwen-flash 或 qwen3-max)
        temperature: 温度参数，控制生成的随机性
        thinking: 是否启用深度思考
        use_postgres_saver: 是否使用PostgresSaver作为checkpointer
        
    Returns:
        配置好的Agent实例
    """
    if model_name == "qwen-flash":
        llm = LangChainQwenChatModel.qwen_flash(
            temperature=temperature,
            thinking=thinking
        )
    elif model_name == "qwen3-max":
        llm = LangChainQwenChatModel.qwen3_max(
            temperature=temperature,
            thinking=thinking
        )
    else:
        raise ValueError(f"Unsupported model: {model_name}")
    
    tools = [
        search_knowledge_base,
        web_search,
        ocr_document,
        understand_image,
        load_skill,
    ]
    
    system_message = SystemMessage(content=SYSTEM_PROMPT)
    
    middlewares = [SkillMiddleware()]
    
    checkpointer = None
    if use_postgres_saver:
        checkpointer = agent_saver_manager.get_postgres_saver()
    
    agent = create_agent(
        llm=llm,
        tools=tools,
        system_message=system_message,
        middlewares=middlewares,
        checkpointer=checkpointer,
    )
    
    return agent


class AgentFactory:
    """Agent工厂类，用于创建不同类型的Agent"""
    
    @staticmethod
    def create_agent(
        agent_type: AgentType = AgentType.GENERAL,
        model_name: str = "qwen-flash",
        temperature: float = 0.7,
        thinking: bool = False,
        use_postgres_saver: bool = True,
    ):
        """创建指定类型的Agent
        
        Args:
            agent_type: Agent类型
            model_name: 模型名称
            temperature: 温度参数
            thinking: 是否启用深度思考
            use_postgres_saver: 是否使用PostgresSaver
            
        Returns:
            配置好的Agent实例
        """
        if agent_type == AgentType.GENERAL:
            return create_general_agent(
                model_name=model_name,
                temperature=temperature,
                thinking=thinking,
                use_postgres_saver=use_postgres_saver,
            )
        else:
            return create_general_agent(
                model_name=model_name,
                temperature=temperature,
                thinking=thinking,
                use_postgres_saver=use_postgres_saver,
            )

