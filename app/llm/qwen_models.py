
import base64

from openai import AsyncOpenAI, OpenAI

from app.config import settings


class QwenChatModel:
    """通义千问聊天模型基类"""
    
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
        """
        同步调用模型
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}, ...]
            
        Returns:
            包含响应内容的字典
        """
        client = self._get_client()
        
        params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
        }
        
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        if self.top_p:
            params["top_p"] = self.top_p
        if self.thinking:
            params["extra_body"] = {"thinking": {"type": "enabled"}}
        if self.stream:
            params["stream"] = True
        
        response = client.chat.completions.create(**params)
        
        if self.stream:
            return self._handle_stream_response(response)
        
        return self._handle_response(response)
    
    async def ainvoke(self, messages):
        """
        异步调用模型
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}, ...]
            
        Returns:
            包含响应内容的字典
        """
        client = self._get_async_client()
        
        params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
        }
        
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        if self.top_p:
            params["top_p"] = self.top_p
        if self.thinking:
            params["extra_body"] = {"thinking": {"type": "enabled"}}
        if self.stream:
            params["stream"] = True
        
        response = await client.chat.completions.create(**params)
        
        if self.stream:
            return await self._ahandle_stream_response(response)
        
        return self._handle_response(response)
    
    def _handle_response(self, response):
        """处理非流式响应"""
        choice = response.choices[0]
        message = choice.message
        
        return {
            "content": message.content or "",
            "thinking_content": getattr(message, "thinking_content", None),
            "reasoning_content": getattr(message, "reasoning_content", None),
            "usage": response.usage.model_dump() if response.usage else None,
            "model_name": self.model_name,
        }
    
    def _handle_stream_response(self, response):
        """处理流式响应"""
        content_parts = []
        thinking_content = ""
        reasoning_content = ""
        
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                if delta.content:
                    content_parts.append(delta.content)
                if hasattr(delta, "thinking_content") and delta.thinking_content:
                    thinking_content += delta.thinking_content
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    reasoning_content += delta.reasoning_content
        
        full_content = "".join(content_parts)
        
        return {
            "content": full_content,
            "thinking_content": thinking_content if thinking_content else None,
            "reasoning_content": reasoning_content if reasoning_content else None,
            "model_name": self.model_name,
        }
    
    async def _ahandle_stream_response(self, response):
        """处理异步流式响应"""
        content_parts = []
        thinking_content = ""
        reasoning_content = ""
        
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                if delta.content:
                    content_parts.append(delta.content)
                if hasattr(delta, "thinking_content") and delta.thinking_content:
                    thinking_content += delta.thinking_content
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    reasoning_content += delta.reasoning_content
        
        full_content = "".join(content_parts)
        
        return {
            "content": full_content,
            "thinking_content": thinking_content if thinking_content else None,
            "reasoning_content": reasoning_content if reasoning_content else None,
            "model_name": self.model_name,
        }


class QwenGeneralModel(QwenChatModel):
    """通义千问通用模型"""
    
    @classmethod
    def qwen_flash(
        cls,
        temperature=0.7,
        max_tokens=None,
        top_p=None,
        stream=False,
        thinking=False,
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
            thinking=thinking
        )
    
    @classmethod
    def qwen3_max(
        cls,
        temperature=0.7,
        max_tokens=None,
        top_p=None,
        stream=False,
        thinking=True,
        api_key=None,
    ):
        """创建qwen3-max模型实例（默认开启深度思考）"""
        return cls(
            model_name="qwen3-max",
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=stream,
            thinking=thinking
        )


class QwenVisionModel(QwenChatModel):
    """通义千问视觉模型"""
    
    @classmethod
    def qwen_vl_ocr(
        cls,
        temperature=0.7,
        max_tokens=None,
        top_p=None,
        stream=False,
        api_key=None,
    ):
        """创建qwen-vl-ocr模型实例"""
        return cls(
            model_name="qwen-vl-ocr",
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=stream,
            thinking=False
        )
    
    @classmethod
    def qwen3_vl_plus(
        cls,
        temperature=0.7,
        max_tokens=None,
        top_p=None,
        stream=False,
        api_key=None,
    ):
        """创建qwen3-vl-plus模型实例"""
        return cls(
            model_name="qwen3-vl-plus",
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=stream,
            thinking=False
        )
    
    def process_image(self, image_path, prompt="请描述这张图片的内容"):
        """处理单张图片"""
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        }]
        
        result = self.invoke(messages)
        return result["content"]
    
    def process_ocr(self, image_path):
        """OCR文字识别"""
        return self.process_image(image_path, prompt="请提取这张图片中的所有文字内容")


class QwenImageModel:
    """通义千问图像生成模型"""
    
    def __init__(self, model_name="z-image-turbo", api_key=None):
        self.model_name = model_name
        self.api_key = api_key or settings.qwen_api_key
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
    
    def generate(self, prompt, size="1024*1024", n=1):
        """生成图像"""
        import httpx
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_name,
            "input": {"prompt": prompt},
            "parameters": {"size": size, "n": n}
        }
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if "output" in result and "results" in result["output"]:
                return [item["url"] for item in result["output"]["results"]]
            return []
    
    async def agenerate(self, prompt, size="1024*1024", n=1):
        """异步生成图像"""
        import httpx
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_name,
            "input": {"prompt": prompt},
            "parameters": {"size": size, "n": n}
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if "output" in result and "results" in result["output"]:
                return [item["url"] for item in result["output"]["results"]]
            return []
    
    @classmethod
    def z_image_turbo(cls, api_key=None):
        """创建z-image-turbo模型实例"""
        return cls(model_name="z-image-turbo", api_key=api_key)
    
    @classmethod
    def qwen_image(cls, api_key=None):
        """创建qwen-image模型实例"""
        return cls(model_name="qwen-image", api_key=api_key)


class QwenCoderModel(QwenChatModel):
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


class QwenTranslationModel:
    """通义千问翻译模型"""
    
    def __init__(self, model_name="qwen-mt-flash", api_key=None):
        self.model_name = model_name
        self.api_key = api_key or settings.qwen_api_key
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    def translate(self, text, source_lang=None, target_lang="en"):
        """翻译文本"""
        import httpx
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"请将以下文本翻译成{target_lang}：\n{text}"
        if source_lang:
            prompt = f"请将以下{source_lang}文本翻译成{target_lang}：\n{text}"
        
        data = {
            "model": self.model_name,
            "input": {"messages": [{"role": "user", "content": prompt}]}
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if "output" in result and "text" in result["output"]:
                return result["output"]["text"]
            return ""
    
    async def atranslate(self, text, source_lang=None, target_lang="en"):
        """异步翻译文本"""
        import httpx
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"请将以下文本翻译成{target_lang}：\n{text}"
        if source_lang:
            prompt = f"请将以下{source_lang}文本翻译成{target_lang}：\n{text}"
        
        data = {
            "model": self.model_name,
            "input": {"messages": [{"role": "user", "content": prompt}]}
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if "output" in result and "text" in result["output"]:
                return result["output"]["text"]
            return ""
    
    @classmethod
    def qwen_mt_flash(cls, api_key=None):
        """创建qwen-mt-flash模型实例"""
        return cls(model_name="qwen-mt-flash", api_key=api_key)
    
    @classmethod
    def qwen_mt_plus(cls, api_key=None):
        """创建qwen-mt-plus模型实例"""
        return cls(model_name="qwen-mt-plus", api_key=api_key)

