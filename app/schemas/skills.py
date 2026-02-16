
from typing import List, Optional
from pydantic import BaseModel, Field


class ImageGenerationRequest(BaseModel):
    """图像生成请求"""
    prompt: str = Field(..., description="图像描述")
    model: Optional[str] = Field("z-image-turbo", description="模型名称：z-image-turbo 或 qwen-image")
    size: Optional[str] = Field("1024*1024", description="图像尺寸")
    n: Optional[int] = Field(1, ge=1, le=4, description="生成数量")


class ImageGenerationResponse(BaseModel):
    """图像生成响应"""
    images: List[str] = Field(..., description="生成的图像URL列表")


class ImageEditingRequest(BaseModel):
    """图像编辑请求"""
    image_path: str = Field(..., description="待编辑图像的路径")
    prompt: str = Field(..., description="编辑指令")
    model: Optional[str] = Field("qwen-image", description="模型名称")
    size: Optional[str] = Field("1024*1024", description="输出图像尺寸")


class ImageEditingResponse(BaseModel):
    """图像编辑响应"""
    images: List[str] = Field(..., description="编辑后的图像URL列表")


class CodingRequest(BaseModel):
    """编程请求"""
    prompt: str = Field(..., description="编程需求描述")
    model: Optional[str] = Field("qwen3-coder-flash", description="模型名称：qwen3-coder-flash 或 qwen3-coder-plus")
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
    model: Optional[str] = Field("qwen-mt-flash", description="模型名称：qwen-mt-flash 或 qwen-mt-plus")


class TranslationResponse(BaseModel):
    """翻译响应"""
    text: str = Field(..., description="翻译后的文本")
    source_lang: Optional[str] = Field(None, description="源语言")
    target_lang: str = Field(..., description="目标语言")
    model_name: str = Field(..., description="使用的模型名称")


class SkillResponse(BaseModel):
    """技能信息响应"""
    name: str = Field(..., description="技能名称")
    description: str = Field(..., description="技能简短描述")


class SkillDetailResponse(SkillResponse):
    """技能详情响应"""
    content: str = Field(..., description="技能详细内容")

