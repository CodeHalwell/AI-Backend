"""
User Model

Represents users who can authenticate and use the API.

Features:
- UUID primary key
- Email-based authentication
- Password hashing
- Role-based access control
- Email verification support
- Soft delete
- Timestamps

Security Considerations:
- Passwords are NEVER stored in plaintext
- Use bcrypt for password hashing
- Email should be unique and indexed
- Consider rate limiting on auth endpoints
"""

import enum

from sqlalchemy import Boolean, Column, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import BaseModel, SoftDeleteMixin


class UserRole(str, enum.Enum):
    """
    User roles for RBAC (Role-Based Access Control).

    Roles:
    - ADMIN: Full system access
    - USER: Standard user access
    - VIEWER: Read-only access

    Why enum?
    - Type safety
    - Prevent invalid values
    - Easy to extend
    - Clear intent
    """
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class User(Base, BaseModel, SoftDeleteMixin):
    """
    User model for authentication and authorization.

    Relationships:
    - agents: AI agents owned by this user
    - conversations: Conversations initiated by this user

    Indexes:
    - email: Unique index for login lookup
    - is_deleted: For filtering active users
    """

    __tablename__ = "users"

    # Basic Information
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User's email address (used for login)",
    )

    hashed_password = Column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password - NEVER store plaintext!",
    )

    full_name = Column(
        String(255),
        nullable=True,
        comment="User's full name",
    )

    # Role and Permissions
    role = Column(
        SQLEnum(UserRole, name="userrole", create_type=False),
        nullable=False,
        default=UserRole.USER,
        server_default="user",
        comment="User role for RBAC",
    )

    # Account Status
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
        comment="Whether user account is active",
    )

    is_verified = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Whether email is verified",
    )

    # Relationships
    # Note: relationships are defined here, but tables are created by SQLAlchemy
    agents = relationship(
        "Agent",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<User {self.email} ({self.role.value})>"

    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN

    @property
    def can_create_agents(self) -> bool:
        """Check if user can create agents."""
        return self.role in (UserRole.ADMIN, UserRole.USER)
