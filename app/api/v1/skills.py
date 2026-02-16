
from typing import List
from fastapi import APIRouter, HTTPException, status

from app.skills import SKILLS, ImageGenerationSkill, ImageEditingSkill, CodingSkill, TranslationSkill
from app.schemas.skills import (
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImageEditingRequest,
    ImageEditingResponse,
    CodingRequest,
    CodingResponse,
    TranslationRequest,
    TranslationResponse,
    SkillResponse,
    SkillDetailResponse,
)

router = APIRouter(prefix="/skills", tags=["技能"])


@router.get("", response_model=List[SkillResponse])
async def get_all_skills():
    """获取所有技能列表"""
    return [{"name": skill["name"], "description": skill["description"]} for skill in SKILLS]


@router.get("/{skill_name}", response_model=SkillDetailResponse)
async def get_skill_detail(skill_name: str):
    """获取技能详情"""
    for skill in SKILLS:
        if skill["name"] == skill_name:
            return {
                "name": skill["name"],
                "description": skill["description"],
                "content": skill["content"]
            }
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Skill '{skill_name}' not found"
    )


@router.post("/image-generation", response_model=ImageGenerationResponse)
async def generate_image(request: ImageGenerationRequest):
    """图像生成"""
    try:
        images = await ImageGenerationSkill.agenerate(
            prompt=request.prompt,
            model=request.model,
            size=request.size,
            n=request.n
        )
        return {"images": images}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image generation failed: {str(e)}"
        )


@router.post("/image-editing", response_model=ImageEditingResponse)
async def edit_image(request: ImageEditingRequest):
    """图像编辑"""
    try:
        images = await ImageEditingSkill.aedit(
            image_path=request.image_path,
            prompt=request.prompt,
            model=request.model,
            size=request.size
        )
        return {"images": images}
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image file not found: {request.image_path}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image editing failed: {str(e)}"
        )


@router.post("/coding", response_model=CodingResponse)
async def generate_code(request: CodingRequest):
    """编程技能"""
    try:
        result = await CodingSkill.acode(
            prompt=request.prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return CodingResponse(
            content=result["content"],
            thinking_content=result.get("thinking_content"),
            reasoning_content=result.get("reasoning_content"),
            model_name=result["model_name"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code generation failed: {str(e)}"
        )


@router.post("/translation", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """翻译技能"""
    try:
        translated_text = await TranslationSkill.atranslate(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            model=request.model
        )
        return TranslationResponse(
            text=translated_text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            model_name=request.model
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )

