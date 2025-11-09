"""
Message Model

Represents individual messages within a conversation.

Features:
- Stores user and AI messages
- Tracks token usage per message
- Supports tool calls and results
- Maintains conversation order

Design:
- Messages belong to conversations
- Can be from user or assistant
- Store tool calls separately for analysis
- Index by conversation for fast retrieval
"""

import enum

from sqlalchemy import JSON, Column, ForeignKey, Integer, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import BaseModel


class MessageRole(str, enum.Enum):
    """
    Message role in conversation.

    Roles:
    - USER: Message from user
    - ASSISTANT: Message from AI assistant
    - SYSTEM: System message (e.g., instructions)
    - TOOL: Tool execution result
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Message(Base, BaseModel):
    """
    Individual message in a conversation.

    Stores:
    - Message content
    - Role (user/assistant/system/tool)
    - Token usage
    - Tool calls if applicable
    """

    __tablename__ = "messages"

    # Relationship
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Conversation this message belongs to",
    )

    # Message Content
    role = Column(
        SQLEnum(MessageRole),
        nullable=False,
        comment="Role: user, assistant, system, or tool",
    )

    content = Column(
        Text,
        nullable=False,
        comment="Message content",
    )

    # Token Usage
    tokens = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of tokens in this message",
    )

    # Tool Calls (for function calling)
    tool_calls = Column(
        JSON,
        nullable=True,
        comment="Tool/function calls made in this message",
    )

    tool_results = Column(
        JSON,
        nullable=True,
        comment="Results from tool executions",
    )

    # Metadata
    metadata = Column(
        JSON,
        nullable=True,
        default=dict,
        comment="Additional message metadata",
    )

    # Relationships
    conversation = relationship(
        "Conversation",
        back_populates="messages",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message {self.role.value}: {content_preview}>"

    @property
    def is_from_user(self) -> bool:
        """Check if message is from user."""
        return self.role == MessageRole.USER

    @property
    def is_from_assistant(self) -> bool:
        """Check if message is from assistant."""
        return self.role == MessageRole.ASSISTANT
