
from typing import List, Optional
from pydantic import BaseModel, Field


class ImageGenerationRequest(BaseModel):
    """图像生成请求"""
    prompt: str = Field(..., description="图像描述")
    model: Optional[str] = Field(None, description="模型名称：z-image-turbo 或 qwen-image。不传则根据 is_expert 参数选择默认模型")
    is_expert: Optional[bool] = Field(False, description="是否使用专家模型：True 使用 qwen-image，False 使用 z-image-turbo")
    size: Optional[str] = Field("1024*1024", description="图像尺寸")
    n: Optional[int] = Field(1, ge=1, le=4, description="生成数量")


class ImageGenerationResponse(BaseModel):
    """图像生成响应"""
    images: List[str] = Field(..., description="生成的图像URL列表")


class ImageEditingRequest(BaseModel):
    """图像编辑请求"""
    image_path: str = Field(..., description="待编辑图像的路径")
    prompt: str = Field(..., description="编辑指令")
    model: Optional[str] = Field(None, description="模型名称。不传则根据 is_expert 参数选择默认模型")
    is_expert: Optional[bool] = Field(False, description="是否使用专家模型")
    size: Optional[str] = Field("1024*1024", description="输出图像尺寸")


class ImageEditingResponse(BaseModel):
    """图像编辑响应"""
    images: List[str] = Field(..., description="编辑后的图像URL列表")


class CodingRequest(BaseModel):
    """编程请求"""
    prompt: str = Field(..., description="编程需求描述")
    model: Optional[str] = Field(None, description="模型名称：qwen3-coder-flash 或 qwen3-coder-plus。不传则根据 is_expert 参数选择默认模型")
    is_expert: Optional[bool] = Field(False, description="是否使用专家模型：True 使用 qwen3-coder-plus，False 使用 qwen3-coder-flash")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="温度参数")
    max_tokens: Optional[int] = Field(None, ge=1, description="最大token数")


class CodingResponse(BaseModel):
    """编程响应"""
    content: str = Field(..., description="生成的代码内容")
    thinking_content: Optional[str] = Field(None, description="思考内容")
    reasoning_content: Optional[str] = Field(None, description="推理内容")
    model_name: str = Field(..., description="使用的模型名称")


class TranslationRequest(BaseModel):
    """翻译请求"""
    text: str = Field(..., description="待翻译文本")
    source_lang: Optional[str] = Field(None, description="源语言，不传则自动检测")
    target_lang: Optional[str] = Field("en", description="目标语言")
    model: Optional[str] = Field(None, description="模型名称：qwen-mt-flash 或 qwen-mt-plus。不传则根据 is_expert 参数选择默认模型")
    is_expert: Optional[bool] = Field(False, description="是否使用专家模型：True 使用 qwen-mt-plus，False 使用 qwen-mt-flash")


class TranslationResponse(BaseModel):
    """翻译响应"""
    text: str = Field(..., description="翻译后的文本")
    source_lang: Optional[str] = Field(None, description="源语言")
    target_lang: str = Field(..., description="目标语言")
    model_name: str = Field(..., description="使用的模型名称")


class ToolResponse(BaseModel):
    """工具信息响应"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具简短描述")


class ToolDetailResponse(ToolResponse):
    """工具详情响应"""
    content: str = Field(..., description="工具详细内容")
