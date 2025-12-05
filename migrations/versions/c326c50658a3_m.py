"""-m

Revision ID: c326c50658a3
Revises: add_paused_enum, remove_time_logs
Create Date: 2025-12-05 12:34:45.686419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c326c50658a3'
down_revision: Union[str, None] = ('add_paused_enum', 'remove_time_logs')
branch_labels: Union[str, Sequence[str], None] = ('Merge migration heads',)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass


