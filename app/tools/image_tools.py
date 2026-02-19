"""图像工具 - 图像生成和编辑"""

from langchain_core.tools import tool
from app.llm.model_factory import ModelFactory


@tool
async def generate_image(prompt: str, size: str = "1024*1024", n: int = 1) -> str:
    """
    根据文本描述生成图像。

    当用户要求生成图像、绘画、设计图、创意图或任何视觉内容时使用此工具。
    支持生成各种风格的图像，如写实、动漫、油画、水彩等。

    Args:
        prompt: 图像的详细描述，越详细效果越好。可以描述场景、物体、风格、光线、颜色等。
        size: 图像尺寸，可选 "1024*1024"(正方形), "1024*768"(横屏), "768*1024"(竖屏)
        n: 生成图像数量，1-4之间

    Returns:
        生成图像的URL列表
    """
    model = ModelFactory.get_image_model(is_turbo=True)
    urls = await model.agenerate(prompt=prompt, size=size, n=n)
    return f"图像已生成：{', '.join(urls)}"


@tool
async def edit_image(image_url: str, prompt: str) -> str:
    """
    根据编辑指令修改现有图像。

    当用户要求修改、优化、变换或编辑已有图像时使用此工具。
    可以执行添加元素、改变风格、调整颜色、替换背景等操作。

    Args:
        image_url: 待编辑图像的URL
        prompt: 编辑指令描述，详细说明想要如何修改图像

    Returns:
        编辑后图像的URL
    """
    model = ModelFactory.get_image_model(is_turbo=True)
    url = await model.aedit_image(image_url=image_url, prompt=prompt)
    return f"图像编辑完成：{url}"
