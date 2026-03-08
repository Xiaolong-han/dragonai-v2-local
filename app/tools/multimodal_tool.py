"""多模态工具 - 图片理解和OCR"""

from langchain_core.tools import tool
from app.llm.dashscope_client import get_dashscope_client
from app.config import settings
from app.utils.image_utils import resolve_image_source_async


@tool
async def understand_image(image_url: str) -> str:
    """
    理解图片内容并描述图片中有什么。

    当用户上传图片并询问图片内容、场景、物体等时使用此工具。

    Args:
        image_url: 待处理图像的路径或URL。可以是相对路径(如 images/xxx.png)、
                   本地绝对路径、或完整的HTTP URL。

    Returns:
        图片内容的详细描述
    """
    client = get_dashscope_client()
    
    resolved_url = await resolve_image_source_async(image_url)
    
    messages = [
        {
            "role": "user",
            "content": [
                {"image": resolved_url},
                {"text": "请详细描述这张图片的内容，包括场景、物体、人物、颜色等细节。"}
            ]
        }
    ]
    
    response = await client.multimodal_call(
        model=settings.model_vision_general,
        messages=messages
    )
    
    return client.parse_text_response(response)


@tool
async def ocr_document(image_url: str) -> str:
    """
    识别图片中的文字内容（OCR）。

    当用户上传图片并需要提取文字时使用此工具, 必须原样完整输出，不要总结、不要省略、不要改写

    Args:
        image_url: 待处理图像的路径或URL。可以是相对路径(如 images/xxx.png)、
                   本地绝对路径、或完整的HTTP URL。

    Returns:
        图片中提取的文字内容
    """
    client = get_dashscope_client()
    
    resolved_url = await resolve_image_source_async(image_url)
    
    messages = [
        {
            "role": "user",
            "content": [
                {"image": resolved_url},
                {"text": "请提取这张图片中的所有文字内容，保持原有格式。"}
            ]
        }
    ]
    
    response = await client.multimodal_call(
        model=settings.model_vision_ocr,
        messages=messages
    )
    
    return client.parse_text_response(response)
