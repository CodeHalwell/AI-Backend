"""
Base Model Mixins

Provides reusable model mixins for common patterns.

Why Mixins?
- DRY principle: Don't repeat common fields
- Consistent behavior across all models
- Easy to maintain and update
- Type hints for better IDE support

Common Patterns:
- TimestampMixin: created_at, updated_at
- UUIDMixin: UUID primary keys
- SoftDeleteMixin: Soft delete support
"""

from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class TimestampMixin:
    """
    Adds timestamp fields to models.

    Fields:
    - created_at: Automatically set on creation
    - updated_at: Automatically updated on modification

    Why automatic timestamps?
    - Audit trail for all records
    - Debug when issues were introduced
    - Track data lifecycle
    - Required for many compliance requirements
    """

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When this record was created",
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="When this record was last updated",
    )


class UUIDMixin:
    """
    UUID primary key mixin.

    Why UUIDs instead of integers?
    - Globally unique (no collisions across databases)
    - Can't guess other IDs (security)
    - Generate client-side if needed
    - Better for distributed systems
    - No auto-increment race conditions

    Trade-offs:
    - Larger storage (16 bytes vs 4-8 bytes)
    - Slightly slower indexing
    - Not human-friendly

    For high-scale AI backends, benefits outweigh costs.
    """

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        comment="Unique identifier",
    )


class SoftDeleteMixin:
    """
    Soft delete support.

    Instead of deleting records, mark them as deleted.

    Why soft delete?
    - Accidental deletion recovery
    - Maintain referential integrity
    - Audit trail preservation
    - Regulatory compliance
    - Can analyze deleted data

    Usage:
        # Soft delete
        user.is_deleted = True
        user.deleted_at = datetime.utcnow()

        # Query only active records
        query = select(User).where(User.is_deleted == False)
    """

    is_deleted = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,  # Index for faster queries
        comment="Whether this record is soft-deleted",
    )

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this record was soft-deleted",
    )


class BaseModel(UUIDMixin, TimestampMixin):
    """
    Base model with UUID and timestamps.

    All models should inherit from this to get:
    - UUID primary key
    - created_at timestamp
    - updated_at timestamp
    """
    pass


__all__ = [
    "TimestampMixin",
    "UUIDMixin",
    "SoftDeleteMixin",
    "BaseModel",
]
