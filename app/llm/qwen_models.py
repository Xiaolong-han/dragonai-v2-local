
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
    
    @classmethod
    def qwen_flash(
        cls,
        temperature=0.7,
        max_tokens=None,
        top_p=None,
        stream=False,
        api_key=None,
    ):
        """创建qwen-flash模型实例"""
        return cls(
            model_name="qwen-flash",
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=stream,
            thinking=False
        )
    
    @classmethod
    def qwen3_max(
        cls,
        temperature=0.7,
        max_tokens=None,
        top_p=None,
        stream=False,
        thinking=False,
        api_key=None,
    ):
        """创建qwen3-max模型实例"""
        return cls(
            model_name="qwen3-max",
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=stream,
            thinking=thinking
        )


class QwenVisionModel(BaseSkillModel):
    """通义千问视觉模型"""

    def __init__(self, model_name="qwen3-vl-plus", api_key=None, **kwargs):
        super().__init__(model_name=model_name, api_key=api_key, **kwargs)
    
    def process_image(self, image_path, prompt="描述这张图片"):
        """处理图片"""
        # 如果是URL，直接使用
        if image_path.startswith(('http://', 'https://')):
            content = [{
                "type": "image_url",
                "image_url": {"url": image_path}
            }]
        else:
            # 如果是本地文件，读取并转为base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            content = [{
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
            }]
        
        content.append({"type": "text", "text": prompt})
        
        messages = [{
            "role": "user",
            "content": content
        }]
        
        result = self.invoke(messages)
        return result.content
    
    def understand_image(self, image_path):
        """理解图片内容"""
        return self.process_image(image_path, prompt="请详细描述这张图片的内容，包括场景、物体、人物、颜色等细节。")
    
    def ocr_image(self, image_path):
        """OCR文字识别"""
        return self.process_image(image_path, prompt="请提取这张图片中的所有文字内容，保持原有格式。")
    
    @classmethod
    def qwen_vl_ocr(cls, api_key=None):
        """创建qwen-vl-ocr模型实例"""
        return cls(model_name="qwen-vl-ocr", api_key=api_key)
    
    @classmethod
    def qwen3_vl_plus(cls, api_key=None):
        """创建qwen3-vl-plus模型实例"""
        return cls(model_name="qwen3-vl-plus", api_key=api_key)


class QwenImageModel:
    """通义千问图像生成模型 - 使用阿里云百炼API (仅支持HTTP同步方式)"""
    
    def __init__(self, model_name="qwen-image-max", api_key=None):
        self.model_name = model_name
        self.api_key = api_key or settings.qwen_api_key
        # 阿里云百炼多模态生成API
        self.base_url = settings.qwen_image_base_url or "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    
    def generate(
        self, 
        prompt: str, 
        size: str = "1024*1024", 
        n: int = 1,
        negative_prompt: str = None,
        prompt_extend: bool = True,
        watermark: bool = False
    ) -> List[str]:
        """
        生成图像 (HTTP同步方式)
        
        Args:
            prompt: 图像描述
            size: 图像尺寸，如 "1024*1024", "1024*768", "768*1024"
            n: 生成数量（当前API可能只支持1张）
            negative_prompt: 负面提示词
            prompt_extend: 是否自动扩展提示词
            watermark: 是否添加水印
            
        Returns:
            图像URL列表
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建请求体，参考阿里云百炼API格式
        data = {
            "model": self.model_name,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            },
            "parameters": {
                "size": size,
                "prompt_extend": prompt_extend,
                "watermark": watermark
            }
        }
        
        # 添加负面提示词（如果提供）
        if negative_prompt:
            data["parameters"]["negative_prompt"] = negative_prompt
        
        with httpx.Client(timeout=120.0) as client:
            response = client.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # 解析响应，提取图像URL
            urls = []
            if "output" in result:
                output = result["output"]
                # 处理不同格式的响应
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
                # 处理choices格式
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
    
    def edit_image(
        self,
        image_url: str,
        prompt: str,
        size: str = "1024*1024",
        negative_prompt: str = None
    ) -> str:
        """
        编辑图像 (HTTP同步方式)
        
        Args:
            image_url: 原图URL
            prompt: 编辑指令
            size: 输出图像尺寸
            negative_prompt: 负面提示词
            
        Returns:
            编辑后的图像URL
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 图像编辑也使用多模态生成API，传入参考图像
        data = {
            "model": self.model_name,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "image": image_url
                            },
                            {
                                "text": f"请编辑这张图片：{prompt}"
                            }
                        ]
                    }
                ]
            },
            "parameters": {
                "size": size
            }
        }
        
        if negative_prompt:
            data["parameters"]["negative_prompt"] = negative_prompt
        
        with httpx.Client(timeout=120.0) as client:
            response = client.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # 解析响应
            if "output" in result:
                output = result["output"]
                if "results" in output and len(output["results"]) > 0:
                    return output["results"][0].get("url") or output["results"][0].get("image_url", "")
                elif "image_url" in output:
                    return output["image_url"]
                elif "url" in output:
                    return output["url"]
            
            return ""
    
    @classmethod
    def z_image_turbo(cls, api_key=None):
        """创建z-image-turbo模型实例"""
        return cls(model_name="z-image-turbo", api_key=api_key)
    
    @classmethod
    def qwen_image(cls, api_key=None):
        """创建qwen-image模型实例"""
        return cls(model_name="qwen-image", api_key=api_key)
    
    @classmethod
    def qwen_image_max(cls, api_key=None):
        """创建qwen-image-max模型实例（推荐）"""
        return cls(model_name="qwen-image-max", api_key=api_key)


class QwenCoderModel(BaseSkillModel):
    """通义千问编程模型"""

    @classmethod
    def qwen3_coder_flash(
        cls,
        temperature=0.7,
        max_tokens=None,
        top_p=None,
        stream=False,
        api_key=None,
    ):
        """创建qwen3-coder-flash模型实例"""
        return cls(
            model_name="qwen3-coder-flash",
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=stream,
            thinking=False
        )
    
    @classmethod
    def qwen3_coder_plus(
        cls,
        temperature=0.7,
        max_tokens=None,
        top_p=None,
        stream=False,
        api_key=None,
    ):
        """创建qwen3-coder-plus模型实例"""
        return cls(
            model_name="qwen3-coder-plus",
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=stream,
            thinking=False
        )


class QwenTranslationModel(BaseSkillModel):
    """通义千问翻译模型"""

    def translate(self, text: str, source_lang: str = None, target_lang: str = "en") -> str:
        """翻译文本"""
        source_text = source_lang if source_lang else "自动检测"
        prompt = f"你是一个专业的翻译助手。请准确翻译用户提供的文本，保持原意和语气。只输出翻译结果。\n\n请将以下{source_text}文本翻译成{target_lang}，只输出翻译结果，不要添加解释：\n\n{text}"
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        result = self.invoke(messages)
        return result.content
    
    async def atranslate(self, text: str, source_lang: str = None, target_lang: str = "en") -> str:
        """异步翻译文本"""
        source_text = source_lang if source_lang else "自动检测"
        prompt = f"你是一个专业的翻译助手。请准确翻译用户提供的文本，保持原意和语气。只输出翻译结果。\n\n请将以下{source_text}文本翻译成{target_lang}，只输出翻译结果，不要添加解释：\n\n{text}"
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        result = await self.ainvoke(messages)
        return result.content
    
    @classmethod
    def qwen_mt_flash(cls, api_key=None):
        """创建qwen-mt-flash模型实例"""
        return cls(model_name="qwen-mt-flash", api_key=api_key)
    
    @classmethod
    def qwen_mt_plus(cls, api_key=None):
        """创建qwen-mt-plus模型实例"""
        return cls(model_name="qwen-mt-plus", api_key=api_key)
