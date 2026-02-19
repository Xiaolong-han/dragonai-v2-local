"""工具模块 - 统一导出所有Agent可用工具"""

from .rag_tool import search_knowledge_base
from .web_search_tool import web_search
from .multimodal_tool import ocr_document, understand_image
from .image_tools import generate_image, edit_image
from .code_tools import code_assist
from .translation_tools import translate_text

# 所有工具列表 - 直接传递给create_agent
ALL_TOOLS = [
    search_knowledge_base,
    web_search,
    ocr_document,
    understand_image,
    generate_image,
    edit_image,
    code_assist,
    translate_text,
]

__all__ = [
    "ALL_TOOLS",
    "search_knowledge_base",
    "web_search",
    "ocr_document",
    "understand_image",
    "generate_image",
    "edit_image",
    "code_assist",
    "translate_text",
]
