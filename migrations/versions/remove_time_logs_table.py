"""remove_time_logs_table

Revision ID: remove_time_logs
Revises: cfafafe9ad38
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'remove_time_logs'
down_revision: Union[str, None] = 'cfafafe9ad38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_time_log_user_id', table_name='time_logs', if_exists=True)
    op.drop_index('idx_time_log_user_date', table_name='time_logs', if_exists=True)
    op.drop_index('idx_time_log_user_created', table_name='time_logs', if_exists=True)
    op.drop_index('idx_time_log_status', table_name='time_logs', if_exists=True)
    op.drop_index('idx_time_log_date', table_name='time_logs', if_exists=True)
    op.drop_index('idx_time_log_created_at', table_name='time_logs', if_exists=True)
    op.drop_index(op.f('ix_time_logs_id'), table_name='time_logs', if_exists=True)
    
    # Drop the table
    op.drop_table('time_logs')
    
    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS timelogstatus")


def downgrade() -> None:
    # Recreate enum type
    op.execute("CREATE TYPE timelogstatus AS ENUM ('ACTIVE', 'PAUSED', 'ON_BREAK', 'COMPLETED')")
    
    # Recreate table
    op.create_table('time_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('log_date', sa.Date(), nullable=False),
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('breaks', sa.Text(), nullable=True),
    sa.Column('total_break_duration', sa.Integer(), nullable=False),
    sa.Column('total_work_duration', sa.Integer(), nullable=True),
    sa.Column('status', sa.Enum('ACTIVE', 'PAUSED', 'ON_BREAK', 'COMPLETED', name='timelogstatus'), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Recreate indexes
    op.create_index('idx_time_log_created_at', 'time_logs', ['created_at'], unique=False)
    op.create_index('idx_time_log_date', 'time_logs', ['log_date'], unique=False)
    op.create_index('idx_time_log_status', 'time_logs', ['status'], unique=False)
    op.create_index('idx_time_log_user_created', 'time_logs', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_time_log_user_date', 'time_logs', ['user_id', 'log_date'], unique=False)
    op.create_index('idx_time_log_user_id', 'time_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_time_logs_id'), 'time_logs', ['id'], unique=False)

