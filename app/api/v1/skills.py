"""技能API - 包含技能元数据管理和专项技能直接触发

路由说明：
- GET /skills - 获取所有技能列表（元数据）
- GET /skills/{skill_name} - 获取技能详情（元数据）
- POST /skills/translation - 翻译
- POST /skills/coding - 编程协助
- POST /skills/image-generation - 图像生成
- POST /skills/image-editing - 图像编辑

注意：
- 如需Agent智能识别意图并调用工具，请使用 POST /api/v1/chat/send
- 直接触发API绕过Agent，直接使用专用模型
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json

from app.tools import ALL_TOOLS
from app.llm.model_factory import ModelFactory
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.skills import (
    SkillResponse, 
    SkillDetailResponse,
    TranslationRequest,
    TranslationResponse,
    CodingRequest,
    CodingResponse,
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImageEditingRequest,
    ImageEditingResponse
)

router = APIRouter(prefix="/skills", tags=["技能"])


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


@router.post("/translation", response_model=TranslationResponse)
async def translate(
    request: TranslationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """翻译接口"""
    try:
        model = ModelFactory.get_translation_model(is_plus=request.is_expert)

        result = await model.atranslate(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )

        return TranslationResponse(
            text=result,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            model_name="expert" if request.is_expert else "fast"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


@router.post("/coding", response_model=CodingResponse)
async def coding(
    request: CodingRequest,
    current_user: User = Depends(get_current_active_user)
):
    """编程协助接口"""
    try:
        model = ModelFactory.get_coder_model(is_plus=request.is_expert)

        messages = [
            {"role": "system", "content": "你是一个专业的编程助手。请提供清晰、高效、有注释的代码，并解释关键逻辑。"},
            {"role": "user", "content": request.prompt}
        ]

        result = await model.ainvoke(messages)

        return CodingResponse(
            content=result.content,
            model_name="expert" if request.is_expert else "fast",
            thinking_content=getattr(result, 'thinking_content', None),
            reasoning_content=getattr(result, 'reasoning_content', None)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"编程协助失败: {str(e)}")


@router.post("/image-generation", response_model=ImageGenerationResponse)
async def image_generation(
    request: ImageGenerationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """图像生成接口"""
    try:
        model = ModelFactory.get_image_model(is_turbo=not request.is_expert)

        urls = await model.agenerate(
            prompt=request.prompt,
            size=request.size or "1024*1024",
            n=request.n or 1
        )

        if not urls:
            raise HTTPException(status_code=500, detail="图像生成失败，未返回URL")

        return ImageGenerationResponse(images=urls)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图像生成失败: {str(e)}")


@router.post("/image-editing", response_model=ImageEditingResponse)
async def image_editing(
    request: ImageEditingRequest,
    current_user: User = Depends(get_current_active_user)
):
    """图像编辑接口"""
    try:
        model = ModelFactory.get_image_edit_model()

        url = await model.aedit_image(
            image_url=request.image_path,
            prompt=request.prompt,
            size=request.size or "1024*1024"
        )

        if not url:
            raise HTTPException(status_code=500, detail="图像编辑失败，未返回URL")

        return ImageEditingResponse(images=[url])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图像编辑失败: {str(e)}")
