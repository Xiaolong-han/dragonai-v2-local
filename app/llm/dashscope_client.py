"""DashScope SDK 统一封装

统一使用 dashscope SDK 调用阿里云百炼 API
支持异步调用封装
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional

import dashscope
from dashscope import Generation, MultiModalConversation

from app.config import settings

logger = logging.getLogger(__name__)


class DashScopeClient:
    """DashScope 客户端封装 - 统一管理 API 调用"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.qwen_api_key
        if not self.api_key:
            raise ValueError("DashScope API key is required. Set qwen_api_key in config or environment.")

    async def _async_call(self, sync_func, *args, **kwargs):
        """将同步调用包装为异步"""
        return await asyncio.to_thread(sync_func, *args, **kwargs)

    async def generation_call(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = None,
        result_format: str = "message",
        **kwargs
    ) -> Dict[str, Any]:
        """调用 Generation API（文本生成）

        用于翻译、编程等文本生成任务

        Args:
            model: 模型名称
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            result_format: 返回格式

        Returns:
            API 响应
        """
        call_kwargs = {
            "model": model,
            "messages": messages,
            "api_key": self.api_key,
            "result_format": result_format,
        }
        if temperature is not None:
            call_kwargs["temperature"] = temperature
        if max_tokens is not None:
            call_kwargs["max_tokens"] = max_tokens
        call_kwargs.update(kwargs)

        response = await self._async_call(Generation.call, **call_kwargs)

        if response.status_code != 200:
            error_msg = f"DashScope API error [{response.status_code}]: {response.message}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        return response

    async def multimodal_call(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """调用 MultiModalConversation API（多模态）

        用于图像生成、图像编辑、OCR、图像识别等多模态任务

        Args:
            model: 模型名称
            messages: 消息列表

        Returns:
            API 响应
        """
        call_kwargs = {
            "model": model,
            "messages": messages,
            "api_key": self.api_key,
        }
        call_kwargs.update(kwargs)

        response = await self._async_call(MultiModalConversation.call, **call_kwargs)

        if response.status_code != 200:
            error_msg = f"DashScope API error [{response.status_code}]: {response.message}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        return response

    def parse_text_response(self, response) -> str:
        """解析文本生成响应

        Args:
            response: Generation.call 返回的响应

        Returns:
            生成的文本内容
        """
        if hasattr(response, 'output') and response.output:
            if hasattr(response.output, 'choices') and response.output.choices:
                choice = response.output.choices[0]
                if hasattr(choice, 'message') and choice.message:
                    return choice.message.content or ""
        return ""

    def parse_image_urls(self, response) -> List[str]:
        """解析图像生成响应中的 URL

        Args:
            response: MultiModalConversation.call 返回的响应

        Returns:
            图像 URL 列表
        """
        urls = []

        if not hasattr(response, 'output') or not response.output:
            return urls

        output = response.output

        if hasattr(output, 'choices') and output.choices:
            for choice in output.choices:
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                if "image" in item:
                                    urls.append(item["image"].strip())
                                elif "image_url" in item:
                                    urls.append(item["image_url"].strip())
                                elif "url" in item:
                                    urls.append(item["url"].strip())
        elif hasattr(output, 'results') and output.results:
            for item in output.results:
                if isinstance(item, dict):
                    if "url" in item:
                        urls.append(item["url"].strip())
                    elif "image_url" in item:
                        urls.append(item["image_url"].strip())
                    elif "image" in item:
                        urls.append(item["image"].strip())

        return urls


_dashscope_client: Optional[DashScopeClient] = None


def get_dashscope_client(api_key: str = None) -> DashScopeClient:
    """获取 DashScope 客户端单例"""
    global _dashscope_client
    if _dashscope_client is None or api_key:
        _dashscope_client = DashScopeClient(api_key)
    return _dashscope_client
