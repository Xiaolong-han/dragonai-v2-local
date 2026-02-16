
from typing import List
from app.llm.qwen_models import QwenImageModel


class ImageGenerationSkill:
    """图像生成技能"""

    @staticmethod
    def generate(
        prompt: str,
        model: str = None,
        is_expert: bool = None,
        size: str = "1024*1024",
        n: int = 1
    ) -> List[str]:
        """
        生成图像

        Args:
            prompt: 图像描述
            model: 模型名称，可选 "z-image-turbo" 或 "qwen-image"
            is_expert: 是否使用专家模型，True 使用 qwen-image，False 使用 z-image-turbo
            size: 图像尺寸，如 "1024*1024"
            n: 生成数量

        Returns:
            生成的图像URL列表
        """
        if model:
            selected_model = model
        elif is_expert:
            selected_model = "qwen-image"
        else:
            selected_model = "z-image-turbo"
        
        if selected_model == "qwen-image":
            image_model = QwenImageModel.qwen_image()
        else:
            image_model = QwenImageModel.z_image_turbo()

        return image_model.generate(prompt, size=size, n=n)

    @staticmethod
    async def agenerate(
        prompt: str,
        model: str = None,
        is_expert: bool = None,
        size: str = "1024*1024",
        n: int = 1
    ) -> List[str]:
        """
        异步生成图像

        Args:
            prompt: 图像描述
            model: 模型名称，可选 "z-image-turbo" 或 "qwen-image"
            is_expert: 是否使用专家模型，True 使用 qwen-image，False 使用 z-image-turbo
            size: 图像尺寸，如 "1024*1024"
            n: 生成数量

        Returns:
            生成的图像URL列表
        """
        if model:
            selected_model = model
        elif is_expert:
            selected_model = "qwen-image"
        else:
            selected_model = "z-image-turbo"
        
        if selected_model == "qwen-image":
            image_model = QwenImageModel.qwen_image()
        else:
            image_model = QwenImageModel.z_image_turbo()

        return await image_model.agenerate(prompt, size=size, n=n)

