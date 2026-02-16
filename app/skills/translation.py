
from app.llm.qwen_models import QwenTranslationModel


class TranslationSkill:
    """翻译技能"""

    @staticmethod
    def translate(
        text: str,
        source_lang: str = None,
        target_lang: str = "en",
        model: str = None,
        is_expert: bool = None
    ) -> str:
        """
        翻译文本

        Args:
            text: 待翻译文本
            source_lang: 源语言，不传则自动检测
            target_lang: 目标语言，默认为 "en"（英语）
            model: 模型名称，可选 "qwen-mt-flash" 或 "qwen-mt-plus"
            is_expert: 是否使用专家模型，True 使用 qwen-mt-plus，False 使用 qwen-mt-flash

        Returns:
            翻译后的文本
        """
        if model:
            selected_model = model
        elif is_expert:
            selected_model = "qwen-mt-plus"
        else:
            selected_model = "qwen-mt-flash"
        
        if selected_model == "qwen-mt-plus":
            translation_model = QwenTranslationModel.qwen_mt_plus()
        else:
            translation_model = QwenTranslationModel.qwen_mt_flash()

        return translation_model.translate(text, source_lang=source_lang, target_lang=target_lang)

    @staticmethod
    async def atranslate(
        text: str,
        source_lang: str = None,
        target_lang: str = "en",
        model: str = None,
        is_expert: bool = None
    ) -> str:
        """
        异步翻译文本

        Args:
            text: 待翻译文本
            source_lang: 源语言，不传则自动检测
            target_lang: 目标语言，默认为 "en"（英语）
            model: 模型名称，可选 "qwen-mt-flash" 或 "qwen-mt-plus"
            is_expert: 是否使用专家模型，True 使用 qwen-mt-plus，False 使用 qwen-mt-flash

        Returns:
            翻译后的文本
        """
        if model:
            selected_model = model
        elif is_expert:
            selected_model = "qwen-mt-plus"
        else:
            selected_model = "qwen-mt-flash"
        
        if selected_model == "qwen-mt-plus":
            translation_model = QwenTranslationModel.qwen_mt_plus()
        else:
            translation_model = QwenTranslationModel.qwen_mt_flash()

        return await translation_model.atranslate(text, source_lang=source_lang, target_lang=target_lang)

