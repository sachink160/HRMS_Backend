"""add paused to timelogstatus enum

Revision ID: add_paused_enum
Revises: 12d20889191e
Create Date: 2025-12-03 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_paused_enum'
down_revision: Union[str, None] = '12d20889191e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'PAUSED' value to the timelogstatus enum
    op.execute("ALTER TYPE timelogstatus ADD VALUE IF NOT EXISTS 'PAUSED'")


def downgrade() -> None:
    # Note: PostgreSQL does not support removing enum values directly
    # This would require recreating the enum type, which is complex
    # For now, we'll leave it as a no-op
    pass

