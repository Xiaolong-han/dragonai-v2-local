
import base64
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

from app.llm.qwen_models import QwenVisionModel
from app.storage import file_storage


@tool
def ocr_document(image_path: str, prompt: Optional[str] = None) -&gt; str:
    """
    使用OCR识别文档或图片中的文字内容

    Args:
        image_path: 图片文件的相对路径或绝对路径
        prompt: 可选的自定义提示词

    Returns:
        OCR识别的文字内容
    """
    if not Path(image_path).exists():
        file_path = file_storage.get_file_path(image_path)
        if not file_path:
            return f"文件不存在: {image_path}"
        image_path = str(file_path)

    ocr_model = QwenVisionModel.qwen_vl_ocr()
    if prompt:
        result = ocr_model.process_image(image_path, prompt)
    else:
        result = ocr_model.process_ocr(image_path)
    return result


@tool
def understand_image(image_path: str, prompt: str = "请描述这张图片的内容") -&gt; str:
    """
    理解并分析图片内容

    Args:
        image_path: 图片文件的相对路径或绝对路径
        prompt: 自定义提示词，用于指导图片理解

    Returns:
        图片理解的分析结果
    """
    if not Path(image_path).exists():
        file_path = file_storage.get_file_path(image_path)
        if not file_path:
            return f"文件不存在: {image_path}"
        image_path = str(file_path)

    vision_model = QwenVisionModel.qwen3_vl_plus()
    result = vision_model.process_image(image_path, prompt)
    return result


def image_to_base64(image_path: str) -&gt; str:
    """
    将图片文件转换为base64编码

    Args:
        image_path: 图片文件路径

    Returns:
        base64编码的字符串
    """
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def build_multimodal_message(
    text: str,
    image_paths: Optional[list[str]] = None,
) -&gt; list[dict]:
    """
    构建多模态消息

    Args:
        text: 文本内容
        image_paths: 图片路径列表

    Returns:
        OpenAI格式的多模态消息列表
    """
    content = [{"type": "text", "text": text}]

    if image_paths:
        for img_path in image_paths:
            if not Path(img_path).exists():
                file_path = file_storage.get_file_path(img_path)
                if file_path:
                    img_path = str(file_path)

            if Path(img_path).exists():
                img_base64 = image_to_base64(img_path)
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"},
                    }
                )

    return [{"role": "user", "content": content}]


__all__ = ["ocr_document", "understand_image", "build_multimodal_message", "image_to_base64"]

