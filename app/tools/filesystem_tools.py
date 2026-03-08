"""文件系统工具 - 文档解析工具

注意：create_deep_agent 内置了以下文件系统工具：
- ls, read_file, write_file, edit_file, glob, grep

本模块只包含业务特定的文档解析工具：read_pdf, read_word
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

from app.config import settings
from app.storage.sandbox import FileSandbox

logger = logging.getLogger(__name__)

STORAGE_DIR = Path(settings.storage_dir).resolve()


def _resolve_path(file_path: str, for_write: bool = False) -> Path:
    """解析文件路径（使用沙箱验证）
    
    Args:
        file_path: 文件路径
        for_write: 是否用于写入操作
        
    Returns:
        解析后的 Path 对象
        
    Raises:
        ValueError: 路径不合法或在沙箱外
    """
    try:
        if for_write:
            return FileSandbox.validate_path_for_write(file_path)
        return FileSandbox.validate_path(file_path)
    except PermissionError as e:
        raise ValueError(str(e))


def _read_pdf_sync(file_path: Path, start_page: int, end_page: Optional[int]) -> tuple:
    """同步读取 PDF 文件，返回 (total_pages, content_parts, total_text, needs_ocr)"""
    from pypdf import PdfReader
    
    reader = PdfReader(str(file_path))
    total_pages = len(reader.pages)
    
    actual_end = end_page if end_page else total_pages
    
    content_parts = []
    content_parts.append(f"PDF 文件: {file_path.name}")
    content_parts.append(f"总页数: {total_pages}")
    content_parts.append(f"读取范围: 第 {start_page} 页 - 第 {actual_end} 页")
    content_parts.append("-" * 50)
    
    total_text = ""
    for page_num in range(start_page - 1, actual_end):
        page = reader.pages[page_num]
        text = page.extract_text()
        if text.strip():
            content_parts.append(f"\n=== 第 {page_num + 1} 页 ===\n")
            content_parts.append(text)
            total_text += text
    
    needs_ocr = not total_text.strip()
    return total_pages, content_parts, total_text, needs_ocr


def _render_pdf_page_sync(file_path: Path, page_num: int) -> str:
    """同步渲染 PDF 页面为 base64 图片"""
    import fitz
    import base64
    
    doc = fitz.open(str(file_path))
    page = doc[page_num]
    mat = fitz.Matrix(2.0, 2.0)
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    doc.close()
    
    img_base64 = base64.b64encode(img_data).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"


@tool
async def read_pdf(file_path: str, start_page: int = 1, end_page: Optional[int] = None, use_ocr: bool = False) -> str:
    """读取 PDF 文件内容。

    当用户上传 PDF 文件并需要提取文字内容时使用此工具。
    支持分页读取，避免一次性读取过多内容。
    
    对于扫描版 PDF（图片型 PDF），会自动检测并提示使用 OCR 模式。

    Args:
        file_path: PDF 文件路径，如 documents/xxx.pdf 或 /documents/xxx.pdf。
        start_page: 开始页码，从 1 开始，默认为 1。
        end_page: 结束页码，不指定则读取到最后一页。
        use_ocr: 是否使用 OCR 模式处理扫描版 PDF。默认 False。
                 当 PDF 是扫描图片时，设置为 True 可提取文字。

    Returns:
        PDF 文件的文本内容，包含页码标记。
    """
    try:
        resolved = _resolve_path(file_path)
    except ValueError as e:
        return f"错误：{e}"
    
    if not resolved.exists():
        return f"错误：文件 '{file_path}' 不存在"
    
    if resolved.suffix.lower() != ".pdf":
        return f"错误：文件 '{file_path}' 不是 PDF 格式"
    
    try:
        total_pages, content_parts, total_text, needs_ocr = await asyncio.to_thread(
            _read_pdf_sync, resolved, start_page, end_page
        )
        
        if start_page < 1:
            start_page = 1
        if start_page > total_pages:
            return f"错误：起始页码 {start_page} 超出范围，PDF 共 {total_pages} 页"
        
        if needs_ocr or use_ocr:
            if not use_ocr and needs_ocr:
                content_parts.append("\n⚠️ 检测到这是扫描版 PDF（无文本层）")
                content_parts.append("请设置 use_ocr=True 来使用 OCR 提取文字")
                return "\n".join(content_parts)
            
            if use_ocr:
                return await _ocr_pdf(resolved, start_page, end_page or total_pages)
        
        return "\n".join(content_parts)
        
    except Exception as e:
        return f"读取 PDF 文件时出错: {str(e)}"


async def _ocr_pdf(file_path: Path, start_page: int, end_page: int) -> str:
    """使用 OCR 处理扫描版 PDF"""
    try:
        import fitz
        from app.llm.dashscope_client import get_dashscope_client
        from app.config import settings
        import base64
        
        total_pages = await asyncio.to_thread(lambda: len(fitz.open(str(file_path))))
        
        content_parts = []
        content_parts.append(f"PDF 文件: {file_path.name}")
        content_parts.append(f"总页数: {total_pages}")
        content_parts.append(f"OCR 读取范围: 第 {start_page} 页 - 第 {end_page} 页")
        content_parts.append("-" * 50)
        
        client = get_dashscope_client()
        
        for page_num in range(start_page - 1, min(end_page, total_pages)):
            img_url = await asyncio.to_thread(_render_pdf_page_sync, file_path, page_num)
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"image": img_url},
                        {"text": "请提取这张图片中的所有文字内容，保持原有格式。只输出文字，不要添加任何说明。"}
                    ]
                }
            ]
            
            response = await client.multimodal_call(
                model=settings.model_vision_ocr,
                messages=messages
            )
            text = client.parse_text_response(response)
            
            content_parts.append(f"\n=== 第 {page_num + 1} 页 ===\n")
            content_parts.append(text)
        
        return "\n".join(content_parts)
        
    except ImportError:
        return "错误：OCR 模式需要安装 PyMuPDF 库。请运行: pip install PyMuPDF"
    except Exception as e:
        return f"OCR 处理 PDF 时出错: {str(e)}"


def _read_word_sync(file_path: Path) -> str:
    """同步读取 Word 文档"""
    from docx import Document
    
    doc = Document(str(file_path))
    
    content_parts = []
    content_parts.append(f"Word 文档: {file_path.name}")
    content_parts.append("-" * 50)
    
    for para in doc.paragraphs:
        if para.text.strip():
            style_name = para.style.name if para.style else "Normal"
            if "Heading" in style_name:
                content_parts.append(f"\n## {para.text}")
            else:
                content_parts.append(para.text)
    
    if doc.tables:
        content_parts.append("\n" + "=" * 50)
        content_parts.append("表格内容:")
        content_parts.append("=" * 50)
        
        for table_idx, table in enumerate(doc.tables, 1):
            content_parts.append(f"\n--- 表格 {table_idx} ---")
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                if row_text.strip(" |"):
                    content_parts.append(row_text)
    
    return "\n".join(content_parts)


@tool
async def read_word(file_path: str) -> str:
    """读取 Word 文档(.docx)内容。

    当用户上传 Word 文档并需要提取文字内容时使用此工具。
    支持读取文档标题、段落、表格等内容。

    Args:
        file_path: Word 文件路径，如 documents/xxx.docx 或 /documents/xxx.docx。

    Returns:
        Word 文档的文本内容，包含结构标记。
    """
    try:
        resolved = _resolve_path(file_path)
    except ValueError as e:
        return f"错误：{e}"
    
    if not resolved.exists():
        return f"错误：文件 '{file_path}' 不存在"
    
    if resolved.suffix.lower() not in [".docx", ".doc"]:
        return f"错误：文件 '{file_path}' 不是 Word 文档格式"
    
    if resolved.suffix.lower() == ".doc":
        return "错误：暂不支持旧版 .doc 格式，请转换为 .docx 格式后重试"
    
    try:
        return await asyncio.to_thread(_read_word_sync, resolved)
    except Exception as e:
        return f"读取 Word 文档时出错: {str(e)}"
