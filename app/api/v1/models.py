
from typing import List
from fastapi import APIRouter

from app.llm.model_factory import ModelFactory, ModelType, ModelName
from app.schemas.models import ChatModelResponse, SkillModelResponse


router = APIRouter(prefix="/models", tags=["模型"])


@router.get("/chat", response_model=List[ChatModelResponse])
async def get_chat_models():
    """获取通用聊天模型列表"""
    available_models = ModelFactory.list_available_models()
    general_models = available_models[ModelType.GENERAL]
    
    models = []
    for model_name in general_models:
        is_expert = model_name == ModelName.QWEN3_MAX
        models.append(ChatModelResponse(
            name=model_name,
            is_expert=is_expert
        ))
    
    return models


@router.get("/skills", response_model=List[SkillModelResponse])
async def get_skill_models():
    """获取专项技能模型列表"""
    skill_models = [
        SkillModelResponse(
            skill_type="coder",
            display_name="编程技能",
            fast_model=ModelName.QWEN3_CODER_FLASH,
            expert_model=ModelName.QWEN3_CODER_PLUS
        ),
        SkillModelResponse(
            skill_type="translation",
            display_name="翻译技能",
            fast_model=ModelName.QWEN_MT_FLASH,
            expert_model=ModelName.QWEN_MT_PLUS
        ),
        SkillModelResponse(
            skill_type="image",
            display_name="图像生成",
            fast_model=ModelName.Z_IMAGE_TURBO,
            expert_model=ModelName.QWEN_IMAGE
        ),
        SkillModelResponse(
            skill_type="vision",
            display_name="视觉模型",
            fast_model=ModelName.QWEN_VL_OCR,
            expert_model=ModelName.QWEN3_VL_PLUS
        )
    ]
    
    return skill_models

