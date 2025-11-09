"""Agent Schemas"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AgentBase(BaseModel):
    """Base agent schema."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    model: str = Field(default="gpt-4-turbo-preview")
    system_prompt: str
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    tools: Optional[List[UUID]] = Field(default_factory=list)
    memory_type: str = Field(default="conversation")
    max_context_messages: int = Field(default=10, ge=1, le=100)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AgentCreate(AgentBase):
    """Schema for creating agent."""
    pass


class AgentUpdate(BaseModel):
    """Schema for updating agent."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=128000)
    tools: Optional[List[UUID]] = None
    memory_type: Optional[str] = None
    max_context_messages: Optional[int] = Field(None, ge=1, le=100)
    metadata: Optional[Dict[str, Any]] = None


class AgentResponse(AgentBase):
    """Schema for agent response."""
    id: UUID
    owner_id: UUID
    total_tokens_used: int
    total_conversations: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


__all__ = ["AgentBase", "AgentCreate", "AgentUpdate", "AgentResponse"]
