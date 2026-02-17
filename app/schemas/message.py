
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, field_validator


class MessageBase(BaseModel):
    role: str = Field(..., max_length=20)
    content: str
    metadata_: Optional[Dict[str, Any]] = Field(None, alias="metadata")

    @field_validator('metadata_', mode='before')
    @classmethod
    def validate_metadata(cls, v):
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        try:
            if hasattr(v, '__dict__'):
                return {}
            return None
        except Exception:
            return None


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    metadata_: Optional[Dict[str, Any]] = Field(None, alias="metadata")


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    conversation_id: int
    content: str
    model_type: Optional[str] = Field("general", description="模型类型: general/vision")
    is_expert: Optional[bool] = Field(False, description="是否使用专家模型")
    images: Optional[List[str]] = Field(None, description="图片URL列表（用于多模态输入）")
    stream: Optional[bool] = Field(True, description="是否使用流式响应")


class ChatMessageItem(BaseModel):
    role: str
    content: str


class ChatHistoryResponse(BaseModel):
    messages: List[MessageResponse]
    total: int

