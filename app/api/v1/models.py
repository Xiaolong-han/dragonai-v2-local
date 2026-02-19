
from typing import List
from fastapi import APIRouter

from app.config import settings
from app.schemas.models import ChatModelResponse, SkillModelResponse


router = APIRouter(prefix="/models", tags=["模型"])


@router.get("/chat", response_model=List[ChatModelResponse])
async def get_chat_models():
    """获取通用聊天模型列表"""
    models = [
        ChatModelResponse(
            name=settings.model_general_fast,
            is_expert=False
        ),
        ChatModelResponse(
            name=settings.model_general_expert,
            is_expert=True
        )
    ]
    return models


@router.get("/skills", response_model=List[SkillModelResponse])
async def get_skill_models():
    """获取专项技能模型列表"""
    skill_models = [
        SkillModelResponse(
            skill_type="coder",
            display_name="编程技能",
            fast_model=settings.model_coder_fast,
            expert_model=settings.model_coder_expert
        ),
        SkillModelResponse(
            skill_type="translation",
            display_name="翻译技能",
            fast_model=settings.model_translation_fast,
            expert_model=settings.model_translation_expert
        ),
        SkillModelResponse(
            skill_type="image",
            display_name="图像生成",
            fast_model=settings.model_image_fast,
            expert_model=settings.model_image_expert
        ),
        SkillModelResponse(
            skill_type="vision",
            display_name="视觉模型",
            fast_model=settings.model_vision_ocr,
            expert_model=settings.model_vision_general
        )
    ]
    return skill_models
