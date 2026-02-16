
from typing import List
from pydantic import BaseModel, Field


class ChatModelResponse(BaseModel):
    """通用聊天模型响应"""
    name: str = Field(..., description="模型名称")
    is_expert: bool = Field(..., description="是否为专家模型，False表示快速模型")


class SkillModelResponse(BaseModel):
    """专项技能模型响应"""
    skill_type: str = Field(..., description="技能类型")
    display_name: str = Field(..., description="技能显示名称")
    fast_model: str = Field(..., description="快速模型名称")
    expert_model: str = Field(..., description="专家模型名称")

