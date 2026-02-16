
from app.llm.qwen_models import (
    QwenGeneralModel,
    QwenVisionModel,
    QwenImageModel,
    QwenCoderModel,
    QwenTranslationModel,
)


class ModelType:
    """模型类型枚举"""
    GENERAL = "general"
    VISION = "vision"
    IMAGE = "image"
    CODER = "coder"
    TRANSLATION = "translation"


class ModelName:
    """模型名称枚举"""
    QWEN_FLASH = "qwen-flash"
    QWEN3_MAX = "qwen3-max"
    QWEN_VL_OCR = "qwen-vl-ocr"
    QWEN3_VL_PLUS = "qwen3-vl-plus"
    Z_IMAGE_TURBO = "z-image-turbo"
    QWEN_IMAGE = "qwen-image"
    QWEN3_CODER_FLASH = "qwen3-coder-flash"
    QWEN3_CODER_PLUS = "qwen3-coder-plus"
    QWEN_MT_FLASH = "qwen-mt-flash"
    QWEN_MT_PLUS = "qwen-mt-plus"


class ModelFactory:
    """通义千问模型工厂"""
    
    _model_cache = {}
    
    @classmethod
    def get_model(
        cls,
        model_name,
        temperature=0.7,
        max_tokens=None,
        top_p=None,
        stream=False,
        thinking=False,
        api_key=None,
        use_cache=True,
    ):
        """
        获取模型实例
        
        Args:
            model_name: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            top_p: top_p参数
            stream: 是否流式输出
            thinking: 是否开启深度思考
            api_key: API密钥
            use_cache: 是否使用缓存
            
        Returns:
            模型实例
        """
        cache_key = f"{model_name}_{temperature}_{max_tokens}_{top_p}_{stream}_{thinking}"
        
        if use_cache and cache_key in cls._model_cache:
            return cls._model_cache[cache_key]
        
        model = cls._create_model(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=stream,
            thinking=thinking,
            api_key=api_key
        )
        
        if use_cache:
            cls._model_cache[cache_key] = model
        
        return model
    
    @classmethod
    def _create_model(
        cls,
        model_name,
        temperature=0.7,
        max_tokens=None,
        top_p=None,
        stream=False,
        thinking=False,
        api_key=None,
    ):
        """
        创建模型实例
        
        Args:
            model_name: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            top_p: top_p参数
            stream: 是否流式输出
            thinking: 是否开启深度思考
            api_key: API密钥
            
        Returns:
            模型实例
        """
        if model_name == ModelName.QWEN_FLASH:
            return QwenGeneralModel.qwen_flash(
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=stream,
                thinking=thinking,
                api_key=api_key
            )
        elif model_name == ModelName.QWEN3_MAX:
            return QwenGeneralModel.qwen3_max(
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=stream,
                thinking=thinking,
                api_key=api_key
            )
        elif model_name == ModelName.QWEN_VL_OCR:
            return QwenVisionModel.qwen_vl_ocr(
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=stream,
                api_key=api_key
            )
        elif model_name == ModelName.QWEN3_VL_PLUS:
            return QwenVisionModel.qwen3_vl_plus(
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=stream,
                api_key=api_key
            )
        elif model_name == ModelName.Z_IMAGE_TURBO:
            return QwenImageModel.z_image_turbo(api_key=api_key)
        elif model_name == ModelName.QWEN_IMAGE:
            return QwenImageModel.qwen_image(api_key=api_key)
        elif model_name == ModelName.QWEN3_CODER_FLASH:
            return QwenCoderModel.qwen3_coder_flash(
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=stream,
                api_key=api_key
            )
        elif model_name == ModelName.QWEN3_CODER_PLUS:
            return QwenCoderModel.qwen3_coder_plus(
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=stream,
                api_key=api_key
            )
        elif model_name == ModelName.QWEN_MT_FLASH:
            return QwenTranslationModel.qwen_mt_flash(api_key=api_key)
        elif model_name == ModelName.QWEN_MT_PLUS:
            return QwenTranslationModel.qwen_mt_plus(api_key=api_key)
        else:
            raise ValueError(f"Unknown model name: {model_name}")
    
    @classmethod
    def get_general_model(
        cls,
        is_expert=False,
        temperature=0.7,
        max_tokens=None,
        top_p=None,
        stream=False,
        thinking=None,
    ):
        """
        获取通用模型
        
        Args:
            is_expert: 是否使用专家模型
            temperature: 温度参数
            max_tokens: 最大token数
            top_p: top_p参数
            stream: 是否流式输出
            thinking: 是否开启深度思考（专家模型默认开启）
            
        Returns:
            QwenGeneralModel实例
        """
        if is_expert:
            model_name = ModelName.QWEN3_MAX
            if thinking is None:
                thinking = True
        else:
            model_name = ModelName.QWEN_FLASH
            if thinking is None:
                thinking = False
        
        return cls.get_model(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=stream,
            thinking=thinking
        )
    
    @classmethod
    def get_vision_model(
        cls,
        is_ocr=False,
        temperature=0.7,
        max_tokens=None,
        top_p=None,
        stream=False,
    ):
        """
        获取视觉模型
        
        Args:
            is_ocr: 是否使用OCR模型
            temperature: 温度参数
            max_tokens: 最大token数
            top_p: top_p参数
            stream: 是否流式输出
            
        Returns:
            QwenVisionModel实例
        """
        if is_ocr:
            model_name = ModelName.QWEN_VL_OCR
        else:
            model_name = ModelName.QWEN3_VL_PLUS
        
        return cls.get_model(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=stream
        )
    
    @classmethod
    def get_image_model(
        cls,
        is_turbo=True,
        api_key=None,
    ):
        """
        获取图像生成模型
        
        Args:
            is_turbo: 是否使用turbo模型
            api_key: API密钥
            
        Returns:
            QwenImageModel实例
        """
        if is_turbo:
            model_name = ModelName.Z_IMAGE_TURBO
        else:
            model_name = ModelName.QWEN_IMAGE
        
        return cls.get_model(
            model_name=model_name,
            api_key=api_key
        )
    
    @classmethod
    def get_coder_model(
        cls,
        is_plus=False,
        temperature=0.7,
        max_tokens=None,
        top_p=None,
        stream=False,
    ):
        """
        获取编程模型
        
        Args:
            is_plus: 是否使用plus模型
            temperature: 温度参数
            max_tokens: 最大token数
            top_p: top_p参数
            stream: 是否流式输出
            
        Returns:
            QwenCoderModel实例
        """
        if is_plus:
            model_name = ModelName.QWEN3_CODER_PLUS
        else:
            model_name = ModelName.QWEN3_CODER_FLASH
        
        return cls.get_model(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=stream
        )
    
    @classmethod
    def get_translation_model(
        cls,
        is_plus=False,
        api_key=None,
    ):
        """
        获取翻译模型
        
        Args:
            is_plus: 是否使用plus模型
            api_key: API密钥
            
        Returns:
            QwenTranslationModel实例
        """
        if is_plus:
            model_name = ModelName.QWEN_MT_PLUS
        else:
            model_name = ModelName.QWEN_MT_FLASH
        
        return cls.get_model(
            model_name=model_name,
            api_key=api_key
        )
    
    @classmethod
    def clear_cache(cls):
        """清除模型缓存"""
        cls._model_cache.clear()
    
    @classmethod
    def list_available_models(cls):
        """
        列出所有可用的模型
        
        Returns:
            按类型分组的模型列表
        """
        return {
            ModelType.GENERAL: [ModelName.QWEN_FLASH, ModelName.QWEN3_MAX],
            ModelType.VISION: [ModelName.QWEN_VL_OCR, ModelName.QWEN3_VL_PLUS],
            ModelType.IMAGE: [ModelName.Z_IMAGE_TURBO, ModelName.QWEN_IMAGE],
            ModelType.CODER: [ModelName.QWEN3_CODER_FLASH, ModelName.QWEN3_CODER_PLUS],
            ModelType.TRANSLATION: [ModelName.QWEN_MT_FLASH, ModelName.QWEN_MT_PLUS],
        }

