
from typing import List
from fastapi import APIRouter

from app.config import settings
from app.schemas.models import ChatModelResponse, ToolModelResponse


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


@router.get("/tools", response_model=List[ToolModelResponse])
async def get_tool_models():
    """获取专项工具模型列表"""
    tool_models = [
        ToolModelResponse(
            tool_type="coder",
            display_name="编程工具",
            fast_model=settings.model_coder_fast,
            expert_model=settings.model_coder_expert
        ),
        ToolModelResponse(
            tool_type="translation",
            display_name="翻译工具",
            fast_model=settings.model_translation_fast,
            expert_model=settings.model_translation_expert
        ),
        ToolModelResponse(
            tool_type="image",
            display_name="图像生成",
            fast_model=settings.model_image_fast,
            expert_model=settings.model_image_expert
        ),
        ToolModelResponse(
            tool_type="vision",
            display_name="视觉模型",
            fast_model=settings.model_vision_ocr,
            expert_model=settings.model_vision_general
        )
    ]
    return tool_models
