
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
    
    def _build_image_content(self, image_path, prompt):
        """构建图片消息内容"""
        if image_path.startswith(('http://', 'https://')):
            content = [{
                "type": "image_url",
                "image_url": {"url": image_path}
            }]
        else:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            content = [{
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
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
        """解析响应中的图像URL"""
        urls = []
        if "output" in result:
            output = result["output"]
            if "results" in output:
                for item in output["results"]:
                    if "url" in item:
                        urls.append(item["url"])
                    elif "image_url" in item:
                        urls.append(item["image_url"])
            elif "image_url" in output:
                urls.append(output["image_url"])
            elif "url" in output:
                urls.append(output["url"])
            elif "choices" in output:
                for choice in output["choices"]:
                    if "message" in choice and "content" in choice["message"]:
                        content = choice["message"]["content"]
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict):
                                    if "image_url" in item:
                                        urls.append(item["image_url"])
                                    elif "url" in item:
                                        urls.append(item["url"])
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
        """生成图像（异步）"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = self._build_generate_data(prompt, size, n, negative_prompt, prompt_extend, watermark)
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return self._parse_image_urls(result)
    
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
            
            if "output" in result:
                output = result["output"]
                if "results" in output and len(output["results"]) > 0:
                    return output["results"][0].get("url") or output["results"][0].get("image_url", "")
                elif "image_url" in output:
                    return output["image_url"]
                elif "url" in output:
                    return output["url"]
            
            return ""
    
    async def aedit_image(
        self,
        image_url: str,
        prompt: str,
        size: str = "1024*1024",
        negative_prompt: str = None
    ) -> str:
        """编辑图像（异步）"""
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
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if "output" in result:
                output = result["output"]
                if "results" in output and len(output["results"]) > 0:
                    return output["results"][0].get("url") or output["results"][0].get("image_url", "")
                elif "image_url" in output:
                    return output["image_url"]
                elif "url" in output:
                    return output["url"]
            
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
