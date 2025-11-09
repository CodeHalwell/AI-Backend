"""
Tool Model

Represents tools/functions that AI agents can call.

Tools enable agents to:
- Execute code
- Query databases
- Call external APIs
- Perform calculations
- Access external data

Security:
- Tools must be explicitly registered
- Input validation required
- Rate limiting on execution
- Audit logging for compliance
"""

from sqlalchemy import JSON, Boolean, Column, Integer, String, Text

from app.db.session import Base
from app.models.base import BaseModel, SoftDeleteMixin


class Tool(Base, BaseModel, SoftDeleteMixin):
    """
    Tool/Function definition for AI agent use.

    Tools are callable functions that agents can use to:
    - Retrieve information
    - Perform actions
    - Interact with external systems

    Examples:
    - get_weather(location)
    - search_database(query)
    - send_email(to, subject, body)
    - calculate(expression)
    """

    __tablename__ = "tools"

    # Basic Information
    name = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique tool name",
    )

    description = Column(
        Text,
        nullable=False,
        comment="Description of what the tool does (shown to AI)",
    )

    # Function Schema (OpenAI function calling format)
    parameters = Column(
        JSON,
        nullable=False,
        comment="JSON Schema for tool parameters",
    )

    # Implementation
    handler = Column(
        String(500),
        nullable=False,
        comment="Python path to handler function (e.g., 'app.tools.weather.get_weather')",
    )

    # Configuration
    is_enabled = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
        comment="Whether tool is currently enabled",
    )

    requires_confirmation = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether tool execution requires user confirmation",
    )

    # Rate Limiting
    max_calls_per_minute = Column(
        Integer,
        nullable=False,
        default=10,
        comment="Maximum calls per minute to prevent abuse",
    )

    # Usage Statistics
    total_calls = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total number of times tool has been called",
    )

    successful_calls = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of successful executions",
    )

    failed_calls = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of failed executions",
    )

    # Metadata
    metadata = Column(
        JSON,
        nullable=True,
        default=dict,
        comment="Additional tool configuration",
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Tool {self.name} (enabled={self.is_enabled})>"

    def increment_calls(self, success: bool = True) -> None:
        """
        Increment usage statistics.

        Args:
            success: Whether the call was successful
        """
        self.total_calls += 1
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1

    @property
    def success_rate(self) -> float:
        """Calculate tool success rate."""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100
