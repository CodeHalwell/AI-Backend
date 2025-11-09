"""
Agent Model

Represents AI agents with specific configurations and capabilities.

An agent is a configured AI assistant with:
- System prompt/instructions
- Model selection (GPT-4, Claude, etc.)
- Temperature and other parameters
- Available tools
- Memory settings

Design Considerations:
- Agent configurations should be versioned
- Support multiple AI providers
- Track token usage and costs
- Allow fine-tuning of parameters
"""

from sqlalchemy import JSON, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import BaseModel, SoftDeleteMixin


class Agent(Base, BaseModel, SoftDeleteMixin):
    """
    AI Agent configuration.

    An agent represents a configured AI assistant with specific:
    - Instructions (system prompt)
    - Model and parameters
    - Available tools
    - Memory settings

    Why store agent configs?
    - Reusability: Create once, use many times
    - Consistency: Same behavior across conversations
    - Versioning: Track changes to agent behavior
    - Analytics: Measure performance per agent type
    """

    __tablename__ = "agents"

    # Basic Information
    name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Agent name for identification",
    )

    description = Column(
        Text,
        nullable=True,
        comment="Description of agent's purpose and capabilities",
    )

    # Owner
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this agent",
    )

    # AI Configuration
    model = Column(
        String(100),
        nullable=False,
        default="gpt-4-turbo-preview",
        comment="AI model to use (e.g., gpt-4, claude-3)",
    )

    system_prompt = Column(
        Text,
        nullable=False,
        comment="System instructions that define agent behavior",
    )

    temperature = Column(
        Float,
        nullable=False,
        default=0.7,
        comment="Temperature for response randomness (0.0-1.0)",
    )

    max_tokens = Column(
        Integer,
        nullable=False,
        default=4096,
        comment="Maximum tokens in response",
    )

    # Tools and Capabilities
    tools = Column(
        JSON,
        nullable=True,
        default=list,
        comment="List of tool IDs available to this agent",
    )

    # Memory Settings
    memory_type = Column(
        String(50),
        nullable=False,
        default="conversation",
        comment="Type of memory: conversation, summary, vector",
    )

    max_context_messages = Column(
        Integer,
        nullable=False,
        default=10,
        comment="Maximum number of messages to keep in context",
    )

    # Metadata
    metadata = Column(
        JSON,
        nullable=True,
        default=dict,
        comment="Additional agent configuration",
    )

    # Usage Statistics (for cost tracking)
    total_tokens_used = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total tokens consumed by this agent",
    )

    total_conversations = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total conversations using this agent",
    )

    # Relationships
    owner = relationship(
        "User",
        back_populates="agents",
        lazy="selectin",
    )

    conversations = relationship(
        "Conversation",
        back_populates="agent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Agent {self.name} (model={self.model})>"

    def increment_usage(self, tokens: int) -> None:
        """
        Increment usage statistics.

        Call this after each AI API call to track costs.
        """
        self.total_tokens_used += tokens
