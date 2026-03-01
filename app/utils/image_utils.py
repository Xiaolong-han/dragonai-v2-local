import base64
import mimetypes
from pathlib import Path


async def resolve_image_source_async(image_source: str) -> str:
    """异步解析图片源，返回可直接使用的URL
    
    支持：
    1. HTTP/HTTPS URL - 原样返回
    2. Base64 数据URI - 原样返回  
    3. 本地相对路径 - 通过 file_storage 解析并编码为 Base64
    4. 本地绝对路径 - 编码为 Base64
    
    Args:
        image_source: 图片源，可以是URL、Base64 URI、相对路径或绝对路径
        
    Returns:
        处理后的URL（可能是原始URL或Base64数据URI）
    """
    if image_source.startswith(('http://', 'https://')):
        return image_source
    
    if image_source.startswith('data:image'):
        return image_source
    
    from app.storage import file_storage
    
    file_path = file_storage.get_file_path(image_source)
    if file_path and file_path.exists():
        return await _encode_local_file(file_path)
    
    abs_path = Path(image_source)
    if abs_path.exists():
        return await _encode_local_file(abs_path)
    
    return image_source


async def _encode_local_file(file_path: Path) -> str:
    """将本地文件编码为Base64数据URI
    
    Args:
        file_path: 本地文件路径
        
    Returns:
        Base64数据URI格式的字符串
    """
    import aiofiles
    
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        mime_type = "image/jpeg"
    
    async with aiofiles.open(file_path, "rb") as f:
        content = await f.read()
        image_data = base64.b64encode(content).decode("utf-8")
    
    return f"data:{mime_type};base64,{image_data}"


async def build_openai_image_content_async(image_url: str, prompt: str) -> list:
    """构建OpenAI格式的图片消息内容
    
    Args:
        image_url: 图片源
        prompt: 文本提示
        
    Returns:
        OpenAI格式的消息内容列表
    """
    resolved_url = await resolve_image_source_async(image_url)
    
    return [
        {"type": "image_url", "image_url": {"url": resolved_url}},
        {"type": "text", "text": prompt}
    ]


async def build_qwen_image_content_async(image_source: str) -> dict:
    """构建阿里百炼格式的图片内容
    
    Args:
        image_source: 图片源
        
    Returns:
        阿里百炼格式的图片内容字典
    """
    resolved_url = await resolve_image_source_async(image_source)
    return {"image": resolved_url}
