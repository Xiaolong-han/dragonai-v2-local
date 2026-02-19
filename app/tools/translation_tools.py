"""翻译工具 - 文本翻译"""

from langchain_core.tools import tool
from app.llm.model_factory import ModelFactory


@tool
async def translate_text(text: str, target_lang: str, source_lang: str = None) -> str:
    """
    将文本翻译成目标语言。

    当用户需要翻译内容、理解外语文本或将内容转换为其他语言时使用此工具。
    支持多种语言之间的互译，包括中文、英语、日语、韩语、法语、德语、西班牙语等。

    Args:
        text: 待翻译的文本内容
        target_lang: 目标语言代码，如 zh(中文)、en(英语)、ja(日语)、ko(韩语)、
                     fr(法语)、de(德语)、es(西班牙语)等
        source_lang: 源语言代码，不传则自动检测

    Returns:
        翻译后的文本
    """
    model = ModelFactory.get_translation_model(is_plus=False)
    result = await model.atranslate(
        text=text,
        source_lang=source_lang,
        target_lang=target_lang
    )
    return result
