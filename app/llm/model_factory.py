"""模型工厂 - 支持配置化模型创建

所有模型名从配置文件读取，避免硬编码
"""

from typing import Optional, Dict, Any

from app.config import settings


class ModelFactory:
    """模型工厂 - 支持配置化模型创建"""

    _model_cache: Dict[str, Any] = {}

    @classmethod
    def get_general_model(cls, is_expert: bool = False, thinking: bool = False, **kwargs):
        """获取通用模型

        使用 LangChain 的 ChatOpenAI 创建模型，支持 bind_tools (用于 Agent)

        Args:
            is_expert: 是否使用专家模型
            thinking: 是否启用深度思考
        """
        from langchain_openai import ChatOpenAI

        model_name = (
            settings.model_general_expert if is_expert
            else settings.model_general_fast
        )

        # 使用 ChatOpenAI 创建模型，支持工具调用 (bind_tools)
        # 启用流式输出
        return ChatOpenAI(
            model=model_name,
            api_key=settings.qwen_api_key,
            base_url=settings.qwen_base_url,
            temperature=0.7,
            streaming=True,  # 启用流式输出
            **kwargs
        )

    @classmethod
    def get_vision_model(cls, is_ocr: bool = False, **kwargs):
        """获取视觉模型

        Args:
            is_ocr: 是否使用OCR专用模型
        """
        from app.llm.qwen_models import QwenVisionModel

        model_name = (
            settings.model_vision_ocr if is_ocr
            else settings.model_vision_general
        )
        return QwenVisionModel(
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
    def get_coder_model(cls, is_plus: bool = False, **kwargs):
        """获取编程模型

        Args:
            is_plus: 是否使用专家模型
        """
        from app.llm.qwen_models import QwenCoderModel

        model_name = (
            settings.model_coder_expert if is_plus
            else settings.model_coder_fast
        )
        return QwenCoderModel(
            model_name=model_name,
            api_key=settings.qwen_api_key,
            **kwargs
        )

    @classmethod
    def get_translation_model(cls, is_plus: bool = False, **kwargs):
        """获取翻译模型

        Args:
            is_plus: 是否使用专家模型
        """
        from app.llm.qwen_models import QwenTranslationModel

        model_name = (
            settings.model_translation_expert if is_plus
            else settings.model_translation_fast
        )
        return QwenTranslationModel(
            model_name=model_name,
            api_key=settings.qwen_api_key,
            **kwargs
        )

    @classmethod
    def clear_cache(cls):
        """清除模型缓存"""
        cls._model_cache.clear()
