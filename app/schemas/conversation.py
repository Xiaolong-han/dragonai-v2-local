
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ConversationBase(BaseModel):
    title: str = Field(..., max_length=200)
    model_name: Optional[str] = None


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    is_pinned: Optional[bool] = None
    model_name: Optional[str] = None


class ConversationResponse(ConversationBase):
    id: int
    user_id: int
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
