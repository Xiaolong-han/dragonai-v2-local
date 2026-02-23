"""多模态工具 - 图片理解和OCR"""

import base64
from langchain_core.tools import tool
from app.llm.model_factory import ModelFactory


def _build_image_content(image_url: str, prompt: str) -> list:
    """构建包含图片的消息内容"""
    content = []
    
    if image_url.startswith(('http://', 'https://')):
        content.append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })
    elif image_url.startswith('data:image'):
        content.append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })
    else:
        from pathlib import Path
        from app.storage import file_storage
        
        file_path = file_storage.get_file_path(image_url)
        if file_path and file_path.exists():
            import mimetypes
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = "image/jpeg"
            
            with open(file_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{image_data}"}
            })
        else:
            abs_path = Path(image_url)
            if abs_path.exists():
                import mimetypes
                mime_type, _ = mimetypes.guess_type(str(abs_path))
                if not mime_type:
                    mime_type = "image/jpeg"
                
                with open(abs_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode("utf-8")
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_data}"}
                })
            else:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": image_url}
                })
    
    content.append({"type": "text", "text": prompt})
    return content


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
    model = ModelFactory.get_vision_model(is_ocr=False)
    
    prompt = "请详细描述这张图片的内容，包括场景、物体、人物、颜色等细节。"
    content = _build_image_content(image_url, prompt)
    messages = [{"role": "user", "content": content}]
    
    result = await model.ainvoke(messages)
    return result.content


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
    model = ModelFactory.get_vision_model(is_ocr=True)
    
    prompt = "请提取这张图片中的所有文字内容，保持原有格式。"
    content = _build_image_content(image_url, prompt)
    messages = [{"role": "user", "content": content}]
    
    result = await model.ainvoke(messages)
    print(f"[OCR_DOCUMENT] 识别结果={result.content}")
    return result.content
