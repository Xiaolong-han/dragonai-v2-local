
import base64
from typing import List
from app.llm.qwen_models import QwenImageModel


class ImageEditingSkill:
    """图像编辑技能"""

    @staticmethod
    def edit(
        image_path: str,
        prompt: str,
        model: str = "qwen-image",
        size: str = "1024*1024"
    ) -> List[str]:
        """
        编辑图像

        Args:
            image_path: 待编辑图像的路径
            prompt: 编辑指令
            model: 模型名称，目前主要使用 "qwen-image"
            size: 输出图像尺寸

        Returns:
            编辑后的图像URL列表
        """
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        import httpx
        from app.config import settings

        api_key = settings.qwen_api_key
        base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2image/image-synthesis"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "input": {
                "prompt": prompt,
                "image": image_base64
            },
            "parameters": {"size": size}
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()

            if "output" in result and "results" in result["output"]:
                return [item["url"] for item in result["output"]["results"]]
            return []

    @staticmethod
    async def aedit(
        image_path: str,
        prompt: str,
        model: str = "qwen-image",
        size: str = "1024*1024"
    ) -> List[str]:
        """
        异步编辑图像

        Args:
            image_path: 待编辑图像的路径
            prompt: 编辑指令
            model: 模型名称，目前主要使用 "qwen-image"
            size: 输出图像尺寸

        Returns:
            编辑后的图像URL列表
        """
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        import httpx
        from app.config import settings

        api_key = settings.qwen_api_key
        base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2image/image-synthesis"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "input": {
                "prompt": prompt,
                "image": image_base64
            },
            "parameters": {"size": size}
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()

            if "output" in result and "results" in result["output"]:
                return [item["url"] for item in result["output"]["results"]]
            return []

