"""rename metadata to extra_data

Revision ID: 001
Revises:
Create Date: 2025-11-09 22:50:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename metadata column to extra_data in agents, messages, and tools tables."""
    # Rename metadata to extra_data in agents table
    op.alter_column('agents', 'metadata', new_column_name='extra_data')

    # Rename metadata to extra_data in messages table
    op.alter_column('messages', 'metadata', new_column_name='extra_data')

    # Rename metadata to extra_data in tools table
    op.alter_column('tools', 'metadata', new_column_name='extra_data')


def downgrade() -> None:
    """Revert extra_data column back to metadata in agents, messages, and tools tables."""
    # Rename extra_data back to metadata in agents table
    op.alter_column('agents', 'extra_data', new_column_name='metadata')

    # Rename extra_data back to metadata in messages table
    op.alter_column('messages', 'extra_data', new_column_name='metadata')

    # Rename extra_data back to metadata in tools table
    op.alter_column('tools', 'extra_data', new_column_name='metadata')
