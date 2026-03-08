"""翻译工具 - 文本翻译"""

import json
from langchain_core.tools import tool
from app.llm.dashscope_client import get_dashscope_client
from app.config import settings


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
        翻译后的文本（JSON格式）
    """
    client = get_dashscope_client()
    
    source_info = source_lang if source_lang else "自动检测"
    
    messages = [
        {"role": "user", "content": f"你是专业翻译助手。准确翻译文本，保持原意和语气，只输出翻译结果。将以下{source_info}文本翻译成{target_lang}：\n\n{text}"}
    ]
    
    response = await client.generation_call(
        model=settings.model_translation_fast,
        messages=messages,
        temperature=0.3
    )
    
    translated_text = client.parse_text_response(response)
    
    return json.dumps({
        "type": "translation",
        "source_lang": source_lang or "auto",
        "target_lang": target_lang,
        "original_text": text[:200] + "..." if len(text) > 200 else text,
        "translated_text": translated_text
    })
