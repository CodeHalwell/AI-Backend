"""
Conversation Model

Represents a conversation session between a user and an AI agent.

Key Features:
- Links user, agent, and messages
- Tracks conversation state
- Stores metadata and context
- Supports conversation summarization

Design:
- One conversation has many messages
- Belongs to one user and one agent
- Can be archived or deleted
- Stores cumulative token usage
"""

import enum

from sqlalchemy import JSON, Column, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import BaseModel, SoftDeleteMixin


class ConversationStatus(str, enum.Enum):
    """
    Conversation status.

    States:
    - ACTIVE: Conversation is ongoing
    - ARCHIVED: Conversation is archived but accessible
    - COMPLETED: Conversation reached natural conclusion
    """
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"


class Conversation(Base, BaseModel, SoftDeleteMixin):
    """
    Conversation between user and AI agent.

    Represents a chat session with:
    - Multiple messages
    - Persistent context
    - Token usage tracking
    - Status management
    """

    __tablename__ = "conversations"

    # Basic Information
    title = Column(
        String(500),
        nullable=True,
        comment="Conversation title (can be auto-generated from first message)",
    )

    # Relationships
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User participating in conversation",
    )

    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="AI agent in conversation",
    )

    # Status
    status = Column(
        SQLEnum(ConversationStatus, name="conversationstatus", create_type=True, native_enum=True),
        nullable=False,
        default=ConversationStatus.ACTIVE,
        server_default="active",
        index=True,
        comment="Current conversation status",
    )

    # Context and Summary
    summary = Column(
        Text,
        nullable=True,
        comment="AI-generated summary of conversation (for long conversations)",
    )

    context = Column(
        JSON,
        nullable=True,
        default=dict,
        comment="Additional context and metadata",
    )

    # Usage Tracking
    total_messages = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total number of messages in conversation",
    )

    total_tokens = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total tokens used in conversation",
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="conversations",
        lazy="selectin",
    )

    agent = relationship(
        "Agent",
        back_populates="conversations",
        lazy="selectin",
    )

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Conversation {self.id} ({self.status.value}, {self.total_messages} messages)>"

    def add_message_count(self, tokens: int = 0) -> None:
        """
        Increment message count and token usage.

        DEPRECATED: This method has a race condition with concurrent updates.
        Use atomic SQL updates instead:

            stmt = (
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(
                    total_messages=Conversation.total_messages + 1,
                    total_tokens=Conversation.total_tokens + tokens
                )
            )
            await db.execute(stmt)

        This method is kept for backward compatibility but should not be used
        in production code with concurrent access.
        """
        import warnings
        warnings.warn(
            "add_message_count() is deprecated due to race conditions. "
            "Use atomic SQL updates with SQLAlchemy's update() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.total_messages += 1
        self.total_tokens += tokens
