"""Create system_logs table for PACK TV.

Revision ID: 0069
Revises: 0068
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0069'
down_revision = '0068'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'system_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('level', sa.String(), nullable=False, server_default='INFO'),
        sa.Column('category', sa.String(), nullable=False, server_default='general'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('correlation_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_system_logs_timestamp', 'timestamp'),
        sa.Index('ix_system_logs_level', 'level'),
        sa.Index('ix_system_logs_category', 'category'),
        sa.Index('ix_system_logs_correlation_id', 'correlation_id'),
        sa.Index('ix_system_logs_user_id', 'user_id'),
    )


def downgrade() -> None:
    op.drop_table('system_logs')
