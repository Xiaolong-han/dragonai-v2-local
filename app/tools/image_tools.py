"""图像工具 - 图像生成和编辑"""

import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import List

import httpx
import aiofiles
from langchain_core.tools import tool

from app.llm.dashscope_client import get_dashscope_client
from app.config import settings
from app.storage import file_storage
from app.security import generate_signed_url
from app.utils.image_utils import resolve_image_source_async

logger = logging.getLogger(__name__)


async def _download_and_save_image(image_url: str, prefix: str = "generated") -> str:
    """下载远程图片并保存到本地存储
    
    Args:
        image_url: 远程图片URL
        prefix: 文件名前缀（generated 或 edited）
        
    Returns:
        带签名的访问URL
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(image_url)
        response.raise_for_status()
        
        content_type = response.headers.get("content-type", "image/png")
        ext = ".png"
        if "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        elif "webp" in content_type:
            ext = ".webp"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{prefix}_{timestamp}_{unique_id}{ext}"
        
        relative_path = f"images/{filename}"
        file_path = file_storage.base_dir / "images" / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(response.content)
        
        return generate_signed_url(relative_path, expires_in_seconds=86400)


@tool
async def generate_image(prompt: str, size: str = "1664*928", n: int = 1) -> str:
    """
    根据文本描述生成图像。

    当用户要求生成图像、绘画、设计图、创意图或任何视觉内容时使用此工具。
    支持生成各种风格的图像，如写实、动漫、油画、水彩等。

    Args:
        prompt: 图像的详细描述，越详细效果越好。可以描述场景、物体、风格、光线、颜色等。
        size: 图像尺寸，可选 "1664*928"(默认), "1024*1024", "1024*768", "768*1024"
        n: 生成图像数量，1-4之间的整数，默认1

    Returns:
        生成图像的URL列表（JSON格式）
    """
    client = get_dashscope_client()
    
    messages = [
        {
            "role": "user",
            "content": [{"text": prompt}]
        }
    ]
    
    response = await client.multimodal_call(
        model=settings.model_image_fast,
        messages=messages,
        size=size,
        n=n
    )
    
    remote_urls = client.parse_image_urls(response)
    
    local_paths = []
    for url in remote_urls:
        try:
            local_path = await _download_and_save_image(url, prefix="generated")
            local_paths.append(local_path)
        except Exception as e:
            logger.warning(f"保存图片失败: {e}, 使用远程URL")
            local_paths.append(url)
    
    return json.dumps({
        "type": "image_generated",
        "prompt": prompt,
        "size": size,
        "urls": local_paths,
        "count": len(local_paths)
    })


@tool
async def edit_image(image_url: str, prompt: str) -> str:
    """
    根据编辑指令修改现有图像。

    当用户要求修改、优化、变换或编辑已有图像时使用此工具。
    可以执行添加元素、改变风格、调整颜色、替换背景等操作。

    Args:
        image_url: 待编辑图像的路径或URL。可以是相对路径(如 images/xxx.png)、
                   本地绝对路径、或完整的HTTP URL。
        prompt: 编辑指令描述，详细说明想要如何修改图像

    Returns:
        编辑后图像的URL（JSON格式）
    """
    client = get_dashscope_client()
    
    resolved_url = await resolve_image_source_async(image_url)
    
    messages = [
        {
            "role": "user",
            "content": [
                {"image": resolved_url},
                {"text": prompt}
            ]
        }
    ]
    
    logger.debug(f"[IMAGE_EDIT] Sending request, model={settings.model_image_edit}")
    
    response = await client.multimodal_call(
        model=settings.model_image_edit,
        messages=messages
    )
    
    urls = client.parse_image_urls(response)
    
    if urls:
        try:
            local_path = await _download_and_save_image(urls[0], prefix="edited")
            result_url = local_path
        except Exception as e:
            logger.warning(f"保存编辑图片失败: {e}, 使用远程URL")
            result_url = urls[0]
    else:
        result_url = ""
    
    return json.dumps({
        "type": "image_edited",
        "prompt": prompt,
        "original_image": image_url,
        "url": result_url
    })
