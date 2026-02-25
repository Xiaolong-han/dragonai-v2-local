"""翻译工具 - 文本翻译"""

from langchain_core.tools import tool
from app.llm.model_factory import ModelFactory


@tool
async def translate_text(text: str, target_lang: str, source_lang: str = None) -> str:
    """
    将文本翻译成目标语言。

    当用户明确要求翻译、或需要将内容转换为其他语言时使用此工具。

    Args:
        text: 待翻译的文本内容
        target_lang: 目标语言代码，如 zh(中文)、en(英语)、ja(日语)、ko(韩语)、fr(法语)、de(德语)、es(西班牙语)
        source_lang: 源语言代码，可选。不传则自动检测源语言

    Returns:
        翻译后的文本
    """
    model = ModelFactory.get_translation_model(is_plus=False)
    
    source_info = source_lang if source_lang else "自动检测"
    
    messages = [
        {"role": "system", "content": "你是专业翻译助手。准确翻译文本，保持原意和语气，只输出翻译结果。"},
        {"role": "user", "content": f"将以下{source_info}文本翻译成{target_lang}：\n\n{text}"}
    ]
    
    result = await model.ainvoke(messages)
    return result.content
