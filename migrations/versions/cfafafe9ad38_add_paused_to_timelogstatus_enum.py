"""add_paused_to_timelogstatus_enum

Revision ID: cfafafe9ad38
Revises: 12d20889191e
Create Date: 2025-12-03 11:26:00.816817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cfafafe9ad38'
down_revision: Union[str, None] = '12d20889191e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass


