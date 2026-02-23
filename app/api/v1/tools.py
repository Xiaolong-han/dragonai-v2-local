"""工具API - 工具元数据管理

路由说明：
- GET /tools - 获取所有工具列表（元数据）
- GET /tools/{tool_name} - 获取工具详情（元数据）

注意：
- 所有工具调用统一通过 POST /api/v1/chat/send 由 Agent 智能处理
- 用户消息可使用前缀格式提示工具意图，如 "翻译：Hello world"
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.tools import ALL_TOOLS
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.tools import ToolResponse, ToolDetailResponse

router = APIRouter(prefix="/tools", tags=["工具"])


@router.get("", response_model=List[ToolResponse])
async def get_all_tools(current_user: User = Depends(get_current_active_user)):
    """获取所有可用工具列表"""
    return [
        {
            "name": tool.name,
            "description": tool.description or ""
        }
        for tool in ALL_TOOLS
    ]


@router.get("/{tool_name}", response_model=ToolDetailResponse)
async def get_tool_detail(tool_name: str, current_user: User = Depends(get_current_active_user)):
    """获取工具详情"""
    for tool in ALL_TOOLS:
        if tool.name == tool_name:
            return {
                "name": tool.name,
                "description": tool.description or "",
                "content": f"这是一个Agent工具，通过聊天调用。可在消息前添加前缀提示工具意图。"
            }
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Tool '{tool_name}' not found"
    )
