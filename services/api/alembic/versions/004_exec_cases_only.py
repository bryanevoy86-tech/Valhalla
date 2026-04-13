"""create just execution_cases table

Revision ID: 004_exec_cases_only
Revises: 20260330_add_updated_ts_to_deals
Create Date: 2026-04-13 18:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_exec_cases_only'
down_revision = '20260330_add_updated_ts_to_deals'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create just execution_cases table"""
    op.create_table(
        'execution_cases',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('intake_id', sa.Integer(), nullable=False),
        sa.Column('assessment_id', sa.Integer(), nullable=True),
        sa.Column('case_type', sa.String(50), nullable=False, server_default='unknown'),
        sa.Column('route_target', sa.String(100), nullable=False, server_default=''),
        sa.Column('current_stage', sa.String(50), nullable=False, server_default='intake'),
        sa.Column('current_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('safe_mode', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('blocked', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('blocker_reason', sa.Text(), nullable=True),
        sa.Column('next_action', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(50), nullable=False, server_default='system'),
        sa.Column('updated_by', sa.String(50), nullable=False, server_default='system'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    # Add FK separately to avoid issues
    op.create_foreign_key('fk_execution_cases_intake', 'execution_cases', 'lead_intake_exec', ['intake_id'], ['id'])
    op.create_unique_constraint('uq_execution_cases_intake', 'execution_cases', ['intake_id'])


def downgrade() -> None:
    """Drop execution_cases table"""
    op.drop_table('execution_cases')
