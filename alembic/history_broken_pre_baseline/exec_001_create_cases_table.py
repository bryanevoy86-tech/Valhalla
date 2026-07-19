"""Create execution layer tables - final version

Revision ID: exec_001_create_cases_table
Revises: add_deal_pipeline_columns
Create Date: 2026-04-13 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'exec_001_create_cases_table'
down_revision = 'add_deal_pipeline_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create execution_cases table"""
    # Check if table exists to prevent errors on re-run
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'execution_cases' not in inspector.get_table_names():
        op.create_table(
            'execution_cases',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('intake_id', sa.Integer(), nullable=False),
            sa.Column('assessment_id', sa.Integer(), nullable=True),
            sa.Column('case_type', sa.String(50), nullable=False),
            sa.Column('route_target', sa.String(100), nullable=False),
            sa.Column('current_stage', sa.String(50), nullable=False),
            sa.Column('current_status', sa.String(50), nullable=False),
            sa.Column('safe_mode', sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column('blocked', sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column('blocker_reason', sa.Text(), nullable=True),
            sa.Column('next_action', sa.Text(), nullable=True),
            sa.Column('created_by', sa.String(50), nullable=False),
            sa.Column('updated_by', sa.String(50), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['intake_id'], ['lead_intake_exec.id'], name='fk_exec_cases_intake'),
            sa.UniqueConstraint('intake_id', name='uq_exec_cases_intake'),
        )


def downgrade() -> None:
    """Drop execution_cases table"""
    op.drop_table('execution_cases', if_exists=True)
