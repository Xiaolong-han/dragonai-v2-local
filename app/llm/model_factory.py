"""模型工厂 - 支持配置化模型创建

所有模型名从配置文件读取，避免硬编码
统一使用异步调用方式
"""

from typing import Optional, List, Dict, Any, Union

from openai import AsyncOpenAI
from langchain_community.chat_models import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings

from app.config import settings


class AsyncSkillModel:
    """异步技能模型 - 用于直接技能触发的模型（视觉/编程/翻译等）"""
    
    def __init__(
        self,
        model_name: str,
        api_key: str = None,
        base_url: str = None,
        temperature: float = 0.7,
        max_tokens: int = None,
        top_p: float = None,
    ):
        self.model_name = model_name
        self.api_key = api_key or settings.qwen_api_key
        self.base_url = base_url or settings.qwen_base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        
        if not self.api_key:
            raise ValueError("Qwen API key is required. Set qwen_api_key in config or environment.")
        
        self._async_client: Optional[AsyncOpenAI] = None
    
    def _get_async_client(self) -> AsyncOpenAI:
        """获取异步客户端"""
        if self._async_client is None:
            self._async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._async_client
    
    async def ainvoke(self, messages: List[Dict[str, Any]], **kwargs) -> Any:
        """异步调用模型"""
        client = self._get_async_client()
        
        request_kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
        }
        
        if self.max_tokens:
            request_kwargs["max_tokens"] = self.max_tokens
        if self.top_p:
            request_kwargs["top_p"] = self.top_p
        
        request_kwargs.update(kwargs)
        
        response = await client.chat.completions.create(**request_kwargs)
        return response.choices[0].message


class ModelFactory:
    """模型工厂 - 支持配置化模型创建"""

    @classmethod
    def get_general_model(cls, is_expert: bool = False, thinking: bool = False, **kwargs) -> ChatTongyi:
        """获取通用模型

        使用 LangChain 的 ChatTongyi 创建模型，支持 bind_tools (用于 Agent)

        Args:
            is_expert: 是否使用专家模型
            thinking: 是否启用深度思考
        """
        model_name = (
            settings.model_general_expert if is_expert
            else settings.model_general_fast
        )
        
        model_kwargs = {}
        if thinking:
            model_kwargs["enable_thinking"] = True
        
        return ChatTongyi(
            model=model_name,
            dashscope_api_key=settings.qwen_api_key,
            streaming=True,
            temperature=0.6 if thinking else 0.7,
            model_kwargs=model_kwargs if model_kwargs else None,
            **kwargs
        )

    @classmethod
    def get_vision_model(cls, is_ocr: bool = False, **kwargs) -> AsyncSkillModel:
        """获取视觉模型

        Args:
            is_ocr: 是否使用OCR专用模型
        """
        model_name = (
            settings.model_vision_ocr if is_ocr
            else settings.model_vision_general
        )
        return AsyncSkillModel(
            model_name=model_name,
            api_key=settings.qwen_api_key,
            **kwargs
        )

    @classmethod
    def get_image_model(cls, is_turbo: bool = True, **kwargs):
        """获取图像生成模型

        注意：图像生成模型使用阿里云百炼多模态生成API，不是OpenAI接口

        Args:
            is_turbo: 是否使用快速模型
        """
        from app.llm.qwen_models import QwenImageModel

        model_name = (
            settings.model_image_fast if is_turbo
            else settings.model_image_expert
        )
        return QwenImageModel(
            model_name=model_name,
            api_key=settings.qwen_api_key
        )

    @classmethod
    def get_image_edit_model(cls, **kwargs):
        """获取图像编辑模型

        注意：图像编辑使用专门的 qwen-image-edit 模型
        """
        from app.llm.qwen_models import QwenImageModel

        return QwenImageModel(
            model_name=settings.model_image_edit,
            api_key=settings.qwen_api_key
        )

    @classmethod
    def get_coder_model(cls, is_plus: bool = False, **kwargs) -> AsyncSkillModel:
        """获取编程模型

        Args:
            is_plus: 是否使用专家模型
        """
        model_name = (
            settings.model_coder_expert if is_plus
            else settings.model_coder_fast
        )
        return AsyncSkillModel(
            model_name=model_name,
            api_key=settings.qwen_api_key,
            **kwargs
        )

    @classmethod
    def get_translation_model(cls, is_plus: bool = False, **kwargs) -> AsyncSkillModel:
        """获取翻译模型

        Args:
            is_plus: 是否使用专家模型
        """
        model_name = (
            settings.model_translation_expert if is_plus
            else settings.model_translation_fast
        )
        return AsyncSkillModel(
            model_name=model_name,
            api_key=settings.qwen_api_key,
            **kwargs
        )
    
    @classmethod
    def get_embedding(cls, model_name: str = None, **kwargs) -> DashScopeEmbeddings:
        """获取Embedding模型

        使用 DashScopeEmbeddings 官方集成

        Args:
            model_name: 模型名称，默认使用配置中的 model_embedding
        """
        return DashScopeEmbeddings(
            model=model_name or settings.model_embedding,
            dashscope_api_key=settings.qwen_api_key,
            **kwargs
        )
