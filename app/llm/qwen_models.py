
import base64
import httpx
from typing import List, Optional

from openai import AsyncOpenAI, OpenAI

from app.config import settings


class BaseSkillModel:
    """技能模型基类 - 用于直接技能触发的模型"""
    
    def __init__(
        self,
        model_name,
        api_key=None,
        base_url=None,
        temperature=0.7,
        max_tokens=None,
        top_p=None,
        stream=False,
        thinking=False,
    ):
        self.model_name = model_name
        self.api_key = api_key or settings.qwen_api_key
        self.base_url = base_url or settings.qwen_base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.stream = stream
        self.thinking = thinking
        
        if not self.api_key:
            raise ValueError("Qwen API key is required. Set qwen_api_key in config or environment.")
        
        self._client = None
        self._async_client = None
    
    def _get_client(self):
        """获取同步客户端"""
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._client
    
    def _get_async_client(self):
        """获取异步客户端"""
        if self._async_client is None:
            self._async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._async_client
    
    def invoke(self, messages):
        """同步调用模型"""
        client = self._get_client()
        
        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "stream": False,
        }
        
        if self.max_tokens:
            kwargs["max_tokens"] = self.max_tokens
        if self.top_p:
            kwargs["top_p"] = self.top_p
        if self.thinking:
            kwargs["extra_body"] = {"enable_thinking": True}
        
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message
    
    async def ainvoke(self, messages):
        """异步调用模型"""
        client = self._get_async_client()
        
        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "stream": False,
        }
        
        if self.max_tokens:
            kwargs["max_tokens"] = self.max_tokens
        if self.top_p:
            kwargs["top_p"] = self.top_p
        if self.thinking:
            kwargs["extra_body"] = {"enable_thinking": True}
        
        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message
    
    def stream(self, messages):
        """同步流式调用"""
        client = self._get_client()
        
        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "stream": True,
        }
        
        if self.max_tokens:
            kwargs["max_tokens"] = self.max_tokens
        if self.top_p:
            kwargs["top_p"] = self.top_p
        if self.thinking:
            kwargs["extra_body"] = {"enable_thinking": True}
        
        return client.chat.completions.create(**kwargs)
    
    async def astream(self, messages):
        """异步流式调用"""
        client = self._get_async_client()
        
        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "stream": True,
        }
        
        if self.max_tokens:
            kwargs["max_tokens"] = self.max_tokens
        if self.top_p:
            kwargs["top_p"] = self.top_p
        if self.thinking:
            kwargs["extra_body"] = {"enable_thinking": True}
        
        return await client.chat.completions.create(**kwargs)


class QwenVisionModel(BaseSkillModel):
    """通义千问视觉模型"""

    def __init__(self, model_name="qwen3-vl-plus", api_key=None, **kwargs):
        super().__init__(model_name=model_name, api_key=api_key, **kwargs)
    
    def _resolve_image_path(self, image_path: str):
        """解析图片路径，返回可读取的文件路径
        
        支持：
        1. HTTP/HTTPS URL - 返回 None（直接使用）
        2. 相对路径 - 通过 file_storage 解析
        3. 绝对路径 - 直接使用
        """
        if image_path.startswith(('http://', 'https://')):
            return None
        
        from app.storage import file_storage
        from pathlib import Path
        
        file_path = file_storage.get_file_path(image_path)
        if file_path and file_path.exists():
            return file_path
        
        abs_path = Path(image_path)
        if abs_path.exists():
            return abs_path
        
        return None

    def _build_image_content(self, image_path, prompt):
        """构建图片消息内容"""
        if image_path.startswith(('http://', 'https://')):
            content = [{
                "type": "image_url",
                "image_url": {"url": image_path}
            }]
        else:
            resolved_path = self._resolve_image_path(image_path)
            if resolved_path:
                import mimetypes
                mime_type, _ = mimetypes.guess_type(str(resolved_path))
                if not mime_type:
                    mime_type = "image/jpeg"
                
                with open(resolved_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode("utf-8")
                content = [{
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_data}"}
                }]
            else:
                content = [{
                    "type": "image_url",
                    "image_url": {"url": image_path}
                }]
        
        content.append({"type": "text", "text": prompt})
        return content
    
    def process_image(self, image_path, prompt="描述这张图片"):
        """处理图片（同步）"""
        content = self._build_image_content(image_path, prompt)
        messages = [{"role": "user", "content": content}]
        result = self.invoke(messages)
        return result.content
    
    async def aprocess_image(self, image_path, prompt="描述这张图片"):
        """处理图片（异步）"""
        content = self._build_image_content(image_path, prompt)
        messages = [{"role": "user", "content": content}]
        result = await self.ainvoke(messages)
        return result.content
    
    def understand_image(self, image_path):
        """理解图片内容（同步）"""
        return self.process_image(image_path, prompt="请详细描述这张图片的内容，包括场景、物体、人物、颜色等细节。")
    
    async def aunderstand_image(self, image_path):
        """理解图片内容（异步）"""
        return await self.aprocess_image(image_path, prompt="请详细描述这张图片的内容，包括场景、物体、人物、颜色等细节。")
    
    def ocr_image(self, image_path):
        """OCR文字识别（同步）"""
        return self.process_image(image_path, prompt="请提取这张图片中的所有文字内容，保持原有格式。")
    
    async def aocr_image(self, image_path):
        """OCR文字识别（异步）"""
        return await self.aprocess_image(image_path, prompt="请提取这张图片中的所有文字内容，保持原有格式。")


class QwenImageModel:
    """通义千问图像生成模型 - 使用阿里云百炼API"""
    
    def __init__(self, model_name="qwen-image-max", api_key=None):
        self.model_name = model_name
        self.api_key = api_key or settings.qwen_api_key
        self.base_url = settings.qwen_image_base_url or "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    
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
            
            with open(file_path, "wb") as f:
                f.write(response.content)
            
            return generate_signed_url(relative_path, expires_in_seconds=86400)
    
    def _build_generate_data(self, prompt, size, n, negative_prompt, prompt_extend, watermark):
        """构建生成请求数据"""
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
                "prompt_extend": prompt_extend,
                "watermark": watermark
            }
        }
        if negative_prompt:
            data["parameters"]["negative_prompt"] = negative_prompt
        return data
    
    def _parse_image_urls(self, result):
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
        
        # 检查错误响应
        if "code" in result and "message" in result:
            error_msg = f"API错误 [{result.get('code')}]: {result.get('message')}"
            raise ValueError(error_msg)
        
        if "output" not in result:
            return urls
            
        output = result["output"]
        
        # 解析 choices 格式（官方标准格式）
        if "choices" in output:
            for choice in output["choices"]:
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                # 官方格式使用 "image" 字段
                                if "image" in item:
                                    urls.append(item["image"].strip())
                                elif "image_url" in item:
                                    urls.append(item["image_url"].strip())
                                elif "url" in item:
                                    urls.append(item["url"].strip())
        
        # 兼容其他可能的格式
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
    
    def generate(
        self, 
        prompt: str, 
        size: str = "1024*1024", 
        n: int = 1,
        negative_prompt: str = None,
        prompt_extend: bool = True,
        watermark: bool = False
    ) -> List[str]:
        """生成图像（同步）"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = self._build_generate_data(prompt, size, n, negative_prompt, prompt_extend, watermark)
        
        with httpx.Client(timeout=120.0) as client:
            response = client.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return self._parse_image_urls(result)
    
    async def agenerate(
        self, 
        prompt: str, 
        size: str = "1024*1024", 
        n: int = 1,
        negative_prompt: str = None,
        prompt_extend: bool = True,
        watermark: bool = False
    ) -> List[str]:
        """生成图像（异步）并保存到本地"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = self._build_generate_data(prompt, size, n, negative_prompt, prompt_extend, watermark)
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            remote_urls = self._parse_image_urls(result)
            
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
    
    def edit_image(
        self,
        image_url: str,
        prompt: str,
        size: str = "1024*1024",
        negative_prompt: str = None
    ) -> str:
        """编辑图像（同步）"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_name,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"image": image_url},
                            {"text": f"请编辑这张图片：{prompt}"}
                        ]
                    }
                ]
            },
            "parameters": {"size": size}
        }
        
        if negative_prompt:
            data["parameters"]["negative_prompt"] = negative_prompt
        
        with httpx.Client(timeout=120.0) as client:
            response = client.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            urls = self._parse_image_urls(result)
            return urls[0] if urls else ""
    
    async def _prepare_image_content(self, image_source: str) -> dict:
        """准备图片内容，支持多种格式
        
        支持：
        1. HTTP/HTTPS URL
        2. Base64 数据URI
        3. 本地相对路径（通过file_storage）
        4. 本地绝对路径
        """
        if image_source.startswith(('http://', 'https://')):
            return {"image": image_source}
        
        if image_source.startswith('data:image'):
            return {"image": image_source}
        
        from app.storage import file_storage
        
        file_path = file_storage.get_file_path(image_source)
        if file_path and file_path.exists():
            return self._encode_local_file(file_path)
        
        from pathlib import Path
        abs_path = Path(image_source)
        if abs_path.exists():
            return self._encode_local_file(abs_path)
        
        return {"image": image_source}
    
    def _encode_local_file(self, file_path) -> dict:
        """将本地文件编码为Base64"""
        import mimetypes
        
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "image/jpeg"
        
        with open(file_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        return {"image": f"data:{mime_type};base64,{image_data}"}

    async def aedit_image(
        self,
        image_url: str,
        prompt: str,
        size: str = "1024*1024",
        negative_prompt: str = None
    ) -> str:
        """编辑图像（异步）"""
        import logging
        logger = logging.getLogger(__name__)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        image_content = await self._prepare_image_content(image_url)
        logger.info(f"[IMAGE_EDIT] 准备图片内容完成, model={self.model_name}")
        
        data = {
            "model": self.model_name,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            image_content,
                            {"text": prompt}
                        ]
                    }
                ]
            },
            "parameters": {"size": size}
        }
        
        if negative_prompt:
            data["parameters"]["negative_prompt"] = negative_prompt
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.base_url, headers=headers, json=data)
            
            if response.status_code != 200:
                try:
                    error_detail = response.json()
                    logger.error(f"[IMAGE_EDIT] API错误详情: {error_detail}")
                    raise ValueError(f"API错误 [{response.status_code}]: {error_detail}")
                except Exception:
                    response.raise_for_status()
            
            result = response.json()
            logger.info(f"[IMAGE_EDIT] API响应: {result}")
            
            urls = self._parse_image_urls(result)
            if urls:
                try:
                    local_path = await self._download_and_save_image(urls[0], prefix="edited")
                    return local_path
                except Exception as e:
                    logger.warning(f"保存编辑图片失败: {e}, 使用远程URL")
                    return urls[0]
            return ""


class QwenCoderModel(BaseSkillModel):
    """通义千问编程模型"""
    pass


class QwenTranslationModel(BaseSkillModel):
    """通义千问翻译模型"""

    def translate(self, text: str, source_lang: str = None, target_lang: str = "en") -> str:
        """翻译文本（同步）"""
        source_text = source_lang if source_lang else "自动检测"
        prompt = f"你是一个专业的翻译助手。请准确翻译用户提供的文本，保持原意和语气。只输出翻译结果。\n\n请将以下{source_text}文本翻译成{target_lang}，只输出翻译结果，不要添加解释：\n\n{text}"
        
        messages = [{"role": "user", "content": prompt}]
        result = self.invoke(messages)
        return result.content
    
    async def atranslate(self, text: str, source_lang: str = None, target_lang: str = "en") -> str:
        """翻译文本（异步）"""
        source_text = source_lang if source_lang else "自动检测"
        prompt = f"你是一个专业的翻译助手。请准确翻译用户提供的文本，保持原意和语气。只输出翻译结果。\n\n请将以下{source_text}文本翻译成{target_lang}，只输出翻译结果，不要添加解释：\n\n{text}"
        
        messages = [{"role": "user", "content": prompt}]
        result = await self.ainvoke(messages)
        return result.content
