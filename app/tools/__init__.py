"""工具模块 - 统一导出所有Agent可用工具"""

from .rag_tool import search_knowledge_base
from .web_search_tool import web_search
from .multimodal_tool import ocr_document, understand_image
from .image_tools import generate_image, edit_image
from .code_tools import code_assist
from .translation_tools import translate_text

# 注意：文件系统工具现在由 FilesystemMiddleware 提供
# 包括: ls, read_file, write_file, edit_file, glob, grep

from .filesystem_tools import read_pdf, read_word

# 所有工具列表 - 直接传递给create_agent
# 文件系统工具 (ls, read_file, write_file, edit_file, glob, grep)
# 现在由 FilesystemMiddleware 自动注入
ALL_TOOLS = [
    search_knowledge_base,
    web_search,
    ocr_document,
    understand_image,
    generate_image,
    edit_image,
    code_assist,
    translate_text,
    read_pdf,
    read_word,
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
    # 文件系统工具由 FilesystemMiddleware 提供
    "read_pdf",
    "read_word",
]
