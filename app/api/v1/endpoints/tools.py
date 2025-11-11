"""Tool Management Endpoints"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.db.session import get_db
from app.models.tool import Tool

router = APIRouter()


# Schemas
class ToolCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str
    parameters: Dict[str, Any]
    handler: str = Field(..., max_length=500)
    requires_confirmation: bool = False
    max_calls_per_minute: int = Field(default=10, ge=1)
    extra_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ToolResponse(BaseModel):
    id: UUID
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: str
    is_enabled: bool
    requires_confirmation: bool
    max_calls_per_minute: int
    total_calls: int
    successful_calls: int
    failed_calls: int
    extra_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    tool_data: ToolCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Register a new tool."""
    # Check if tool name already exists
    result = await db.execute(
        select(Tool).where(Tool.name == tool_data.name)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Tool name already exists")

    tool = Tool(**tool_data.model_dump())
    db.add(tool)
    await db.commit()
    await db.refresh(tool)

    return tool


@router.get("", response_model=List[ToolResponse])
async def list_tools(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    only_enabled: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List available tools."""
    query = select(Tool).where(~Tool.is_deleted)

    if only_enabled:
        query = query.where(Tool.is_enabled)

    result = await db.execute(query.offset(skip).limit(limit))
    tools = result.scalars().all()

    return tools


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get tool by ID."""
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalar_one_or_none()

    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    return tool
