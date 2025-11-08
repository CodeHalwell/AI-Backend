"""Conversation Schemas"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.conversation import ConversationStatus


class ConversationCreate(BaseModel):
    """Schema for creating conversation."""
    agent_id: UUID
    title: Optional[str] = Field(None, max_length=500)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ConversationUpdate(BaseModel):
    """Schema for updating conversation."""
    title: Optional[str] = Field(None, max_length=500)
    status: Optional[ConversationStatus] = None
    context: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """Schema for conversation response."""
    id: UUID
    user_id: UUID
    agent_id: UUID
    title: Optional[str]
    status: ConversationStatus
    summary: Optional[str]
    context: Optional[Dict[str, Any]]
    total_messages: int
    total_tokens: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Schema for creating message."""
    content: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    tokens: int
    tool_calls: Optional[Dict[str, Any]]
    tool_results: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True


__all__ = [
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "MessageCreate",
    "MessageResponse",
]
