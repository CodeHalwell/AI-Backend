"""
Database Models

All SQLAlchemy models are imported here for easy access.

Import Order:
1. Base models (mixins)
2. Independent models (User, Tool)
3. Dependent models (Agent, Conversation, Message)

Why this matters:
- Ensures proper model registration with SQLAlchemy
- Prevents circular import issues
- Makes models available for Alembic migrations
"""

from app.models.agent import Agent
from app.models.base import BaseModel, SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message, MessageRole
from app.models.tool import Tool
from app.models.user import User, UserRole

__all__ = [
    # Base
    "BaseModel",
    "TimestampMixin",
    "UUIDMixin",
    "SoftDeleteMixin",
    # User
    "User",
    "UserRole",
    # Agent
    "Agent",
    # Conversation
    "Conversation",
    "ConversationStatus",
    # Message
    "Message",
    "MessageRole",
    # Tool
    "Tool",
]
