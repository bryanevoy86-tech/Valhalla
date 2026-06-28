"""Add go_live_state table for governance control plane.

Revision ID: 20260527_add_go_live_state
Revises: 20260508_add_property_intel
Create Date: 2026-05-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260527_add_go_live_state'
down_revision = '20260508_add_property_intel'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create go_live_state table
    op.create_table(
        'go_live_state',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('go_live_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('kill_switch_engaged', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('changed_by', sa.String(), nullable=True),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_go_live_state'))
    )


def downgrade() -> None:
    op.drop_table('go_live_state')
