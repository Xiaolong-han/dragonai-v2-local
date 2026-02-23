
from typing import List
from pydantic import BaseModel, Field


class ToolResponse(BaseModel):
    """工具信息响应"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具简短描述")


class ToolDetailResponse(ToolResponse):
    """工具详情响应"""
    content: str = Field(..., description="工具详细内容")
