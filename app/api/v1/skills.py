"""技能API - 包含技能元数据管理和专项技能直接触发

路由说明：
- GET /skills - 获取所有技能列表（元数据）
- GET /skills/{skill_name} - 获取技能详情（元数据）
- POST /skills/direct/image/generate - 直接触发图像生成
- POST /skills/direct/image/edit - 直接触发图像编辑
- POST /skills/direct/code/assist - 直接触发编程协助
- POST /skills/direct/translate - 直接触发翻译

注意：
- 如需Agent智能识别意图并调用工具，请使用 POST /api/v1/chat/send
- 直接触发API绕过Agent，直接使用专用模型
"""

from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json

from app.tools import ALL_TOOLS
from app.llm.model_factory import ModelFactory
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.skills import SkillResponse, SkillDetailResponse

router = APIRouter(prefix="/skills", tags=["技能"])


class ImageGenerateRequest(BaseModel):
    """图像生成请求"""
    prompt: str = Field(..., description="图像描述")
    size: str = Field("1024*1024", description="图像尺寸")
    n: int = Field(1, ge=1, le=4, description="生成数量")
    model_mode: Literal["fast", "expert"] = Field("fast", description="模型模式")
    negative_prompt: Optional[str] = Field(None, description="负面提示词")
    prompt_extend: bool = Field(True, description="是否自动扩展提示词")


class ImageEditRequest(BaseModel):
    """图像编辑请求"""
    image_url: str = Field(..., description="原图URL")
    prompt: str = Field(..., description="编辑指令")
    size: str = Field("1024*1024", description="输出图像尺寸")
    model_mode: Literal["fast", "expert"] = Field("fast", description="模型模式")
    negative_prompt: Optional[str] = Field(None, description="负面提示词")


class CodeAssistRequest(BaseModel):
    """编程协助请求"""
    prompt: str = Field(..., description="编程需求")
    language: str = Field("python", description="编程语言")
    model_mode: Literal["fast", "expert"] = Field("fast", description="模型模式")
    stream: bool = Field(True, description="是否流式响应")


class TranslateRequest(BaseModel):
    """翻译请求"""
    text: str = Field(..., description="待翻译文本")
    target_lang: str = Field(..., description="目标语言")
    source_lang: Optional[str] = Field(None, description="源语言")
    model_mode: Literal["fast", "expert"] = Field("fast", description="模型模式")


@router.get("", response_model=List[SkillResponse])
async def get_all_skills():
    """获取所有可用技能列表"""
    return [
        {
            "name": tool.name,
            "description": tool.description or ""
        }
        for tool in ALL_TOOLS
    ]


@router.get("/{skill_name}", response_model=SkillDetailResponse)
async def get_skill_detail(skill_name: str):
    """获取技能详情"""
    for tool in ALL_TOOLS:
        if tool.name == skill_name:
            return {
                "name": tool.name,
                "description": tool.description or "",
                "content": f"这是一个Agent工具，可以通过主聊天调用或在专项技能页面直接使用。"
            }
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Skill '{skill_name}' not found"
    )


@router.post("/direct/image/generate")
async def direct_image_generate(
    request: ImageGenerateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """直接触发图像生成 - 不经过Agent"""
    try:
        model = ModelFactory.get_image_model(
            is_turbo=request.model_mode == "fast"
        )

        urls = await model.agenerate(
            prompt=request.prompt,
            size=request.size,
            n=request.n,
            negative_prompt=request.negative_prompt,
            prompt_extend=request.prompt_extend
        )

        if not urls:
            raise HTTPException(status_code=500, detail="图像生成失败，未返回URL")

        return {
            "success": True,
            "data": {
                "urls": urls,
                "prompt": request.prompt,
                "count": len(urls)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图像生成失败: {str(e)}")


@router.post("/direct/image/edit")
async def direct_image_edit(
    request: ImageEditRequest,
    current_user: User = Depends(get_current_active_user)
):
    """直接触发图像编辑 - 不经过Agent"""
    try:
        model = ModelFactory.get_image_model(
            is_turbo=request.model_mode == "fast"
        )

        url = await model.aedit_image(
            image_url=request.image_url,
            prompt=request.prompt,
            size=request.size,
            negative_prompt=request.negative_prompt
        )

        if not url:
            raise HTTPException(status_code=500, detail="图像编辑失败，未返回URL")

        return {
            "success": True,
            "data": {
                "url": url,
                "prompt": request.prompt
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图像编辑失败: {str(e)}")


@router.post("/direct/code/assist")
async def direct_code_assist(
    request: CodeAssistRequest,
    current_user: User = Depends(get_current_active_user)
):
    """直接触发编程协助 - 不经过Agent"""
    try:
        if request.stream:
            async def event_generator():
                model = ModelFactory.get_coder_model(
                    is_plus=request.model_mode == "expert"
                )

                messages = [
                    {"role": "system", "content": f"你是一个专业的{request.language}编程助手。请提供清晰、高效、有注释的代码，并解释关键逻辑。"},
                    {"role": "user", "content": request.prompt}
                ]

                async for chunk in model.astream(messages):
                    yield f"data: {json.dumps({'type': 'content', 'data': chunk.content})}\n\n"

                yield "data: [DONE]\n\n"

            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream"
            )
        else:
            model = ModelFactory.get_coder_model(
                is_plus=request.model_mode == "expert"
            )

            messages = [
                {"role": "system", "content": f"你是一个专业的{request.language}编程助手。请提供清晰、高效、有注释的代码，并解释关键逻辑。"},
                {"role": "user", "content": request.prompt}
            ]

            result = await model.ainvoke(messages)

            return {
                "success": True,
                "data": {
                    "content": result.content
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"编程协助失败: {str(e)}")


@router.post("/direct/translate")
async def direct_translate(
    request: TranslateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """直接触发翻译 - 不经过Agent"""
    try:
        model = ModelFactory.get_translation_model(
            is_plus=request.model_mode == "expert"
        )

        result = await model.atranslate(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )

        return {
            "success": True,
            "data": {
                "original": request.text,
                "translated": result,
                "source_lang": request.source_lang or "auto",
                "target_lang": request.target_lang
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")
