"""多模态工具 - 图片理解和OCR"""

from langchain_core.tools import tool
from app.llm.model_factory import ModelFactory


@tool
async def understand_image(image_url: str) -> str:
    """
    理解图片内容并描述图片中有什么。

    当用户上传图片并询问图片内容、场景、物体等时使用此工具。

    Args:
        image_url: 图片的URL地址

    Returns:
        图片内容的详细描述
    """
    model = ModelFactory.get_vision_model(is_ocr=False)
    result = await model.aunderstand_image(image_url)
    return result


@tool
async def ocr_document(image_url: str) -> str:
    """
    识别图片中的文字内容（OCR）。

    当用户上传包含文字的图片（如截图、文档照片、名片等）并需要提取文字时使用此工具。

    Args:
        image_url: 图片的URL地址

    Returns:
        图片中提取的文字内容
    """
    model = ModelFactory.get_vision_model(is_ocr=True)
    result = await model.aocr_image(image_url)
    return result
