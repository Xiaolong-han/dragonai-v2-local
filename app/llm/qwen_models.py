"""Qwen 图像生成模型

图像生成/编辑模型使用阿里云百炼多模态生成API（非OpenAI兼容接口）
仅支持异步调用
"""

import httpx
from typing import List, Optional

from app.config import settings


class QwenImageModel:
    """通义千问图像生成模型 - 使用阿里云百炼API(仅异步http client)
    生成图像:支持qwen-image, qwen-image-plus, qwen-image-max
    图像编辑:支持qwen-image-edit, qwen-image-edit-plus, qwen-image-edit-max
    """
    
    def __init__(self, model_name: str = "qwen-image", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key or settings.qwen_api_key
        self.base_url = settings.qwen_image_base_url
    
    async def _download_and_save_image(self, image_url: str, prefix: str = "generated") -> str:
        """下载远程图片并保存到本地存储
        
        Args:
            image_url: 远程图片URL
            prefix: 文件名前缀（generated 或 edited）
            
        Returns:
            带签名的访问URL
        """
        import uuid
        from datetime import datetime
        from pathlib import Path
        from app.storage import file_storage
        from app.core.security import generate_signed_url
        
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
            
            import aiofiles
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(response.content)
            
            return generate_signed_url(relative_path, expires_in_seconds=86400)
    
    def _build_generate_data(self, prompt, size, n, negative_prompt, prompt_extend, watermark):
        """构建生成请求数据
        """
        data = {
            "model": self.model_name,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ]
            },
            "parameters": {
                "size": size,
                "n": n,
                "prompt_extend": prompt_extend,
                "watermark": watermark
            }
        }
        if negative_prompt:
            data["parameters"]["negative_prompt"] = negative_prompt
        return data

    def _build_edit_data(self, image_content, prompt, size, n, negative_prompt, prompt_extend, watermark):
        """构建编辑请求数据
        """
        data = {
            "model": self.model_name,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [image_content, {"text": prompt}]
                    }
                ]
            },
            "parameters": {
                "n": n,
                "prompt_extend": prompt_extend,
                "watermark": watermark
            }
        }
        if size:
            data["parameters"]["size"] = size
        if negative_prompt:
            data["parameters"]["negative_prompt"] = negative_prompt
        return data
    
    def _parse_image_urls(self, result) -> List[str]:
        """解析响应中的图像URL
        
        阿里官方返回格式：
        {
            "output": {
                "choices": [{
                    "finish_reason": "stop",
                    "message": {
                        "content": [{"image": "url"}],
                        "role": "assistant"
                    }
                }],
                "task_metric": {"FAILED": 0, "SUCCEEDED": 1, "TOTAL": 1}
            }
        }
        """
        urls = []
        # 检查是否有错误信息，code和message都是请求失败才会返回
        if "code" in result and "message" in result:
            error_msg = f"API错误 [{result.get('code')}]: {result.get('message')}"
            raise ValueError(error_msg)
        # 检查是否有输出
        if "output" not in result:
            return urls
            
        output = result["output"]
        # 检查是否有生成结果
        if "choices" in output:
            for choice in output["choices"]:
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                if "image" in item:
                                    urls.append(item["image"].strip())
                                elif "image_url" in item:
                                    urls.append(item["image_url"].strip())
                                elif "url" in item:
                                    urls.append(item["url"].strip())
        # ？
        elif "results" in output:
            for item in output["results"]:
                if "url" in item:
                    urls.append(item["url"].strip())
                elif "image_url" in item:
                    urls.append(item["image_url"].strip())
                elif "image" in item:
                    urls.append(item["image"].strip())
        elif "image_url" in output:
            urls.append(output["image_url"].strip())
        elif "url" in output:
            urls.append(output["url"].strip())
        elif "image" in output:
            urls.append(output["image"].strip())
        
        return urls
    
    async def agenerate(
        self, 
        prompt: str, 
        size: str = "1664*928", # 1664*928
        n: int = 1,
        negative_prompt: str = None,
        prompt_extend: bool = True,
        watermark: bool = False
    ) -> List[str]:
        """生成图像（异步）并保存到本地"""
        # 1. 构建请求头， 参考阿里百炼文档
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # 2. 构建请求数据， 参考阿里百炼文档
        data = self._build_generate_data(prompt, size, n, negative_prompt, prompt_extend, watermark)
        # 3. 发送异步请求，超时时间120秒
        async with httpx.AsyncClient(timeout=120.0) as client:
            # 4. 处理响应
            response = await client.post(self.base_url, headers=headers, json=data)
            # 4.1 检查响应状态码
            response.raise_for_status()
            # 4.2 解析响应中的图像URL
            result = response.json()
            remote_urls = self._parse_image_urls(result)
            # 4.3 下载并保存图像
            local_paths = []
            for url in remote_urls:
                try:
                    local_path = await self._download_and_save_image(url, prefix="generated")
                    local_paths.append(local_path)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"保存图片失败: {e}, 使用远程URL")
                    local_paths.append(url)
            
            return local_paths
    
    async def _prepare_image_content(self, image_source: str) -> dict:
        """准备图片内容，支持多种格式"""
        from app.utils.image_utils import build_qwen_image_content_async
        return await build_qwen_image_content_async(image_source)

    async def aedit_image(
        self,
        image_url: str,
        prompt: str,
        size: str = None, # 不指定时，总像素数接近 1024*1024，宽高比与输入图像相同
        n: int = 1,
        negative_prompt: str = None,
        prompt_extend: bool = True,
        watermark: bool = False
    ) -> str:
        """编辑图像（异步），当前仅支持单张图像编辑"""
        import logging
        logger = logging.getLogger(__name__)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        image_content = await self._prepare_image_content(image_url)
        logger.debug(f"[IMAGE_EDIT] Prepared image content, model={self.model_name}")
        
        data = self._build_edit_data(image_content, prompt, size, n, negative_prompt, prompt_extend, watermark)
        
        async with httpx.AsyncClient(timeout=240.0) as client:
            logger.debug(f"[IMAGE_EDIT] Sending request, model={self.model_name}")

            response = await client.post(self.base_url, headers=headers, json=data)
            
            if response.status_code != 200:
                try:
                    error_detail = response.json()
                    logger.error(f"[IMAGE_EDIT] API error: {error_detail}")
                    raise ValueError(f"API error [{response.status_code}]: {error_detail}")
                except Exception:
                    response.raise_for_status()
            
            result = response.json()
            logger.debug(f"[IMAGE_EDIT] API response received")
            
            urls = self._parse_image_urls(result)
            if urls:
                try:
                    local_path = await self._download_and_save_image(urls[0], prefix="edited")
                    return local_path
                except Exception as e:
                    logger.warning(f"Failed to save edited image: {e}, using remote URL")
                    return urls[0]
            return ""
