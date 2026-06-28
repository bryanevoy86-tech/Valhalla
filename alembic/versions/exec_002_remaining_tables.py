"""Create remaining execution layer tables

Revision ID: exec_002_remaining_tables
Revises: exec_001_create_cases_table
Create Date: 2026-04-13 21:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'exec_002_remaining_tables'
down_revision = 'exec_001_create_cases_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create execution_events, execution_tasks, execution_assessments tables"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    table_names = inspector.get_table_names()
    
    # Create execution_events
    if 'execution_events' not in table_names:
        op.create_table(
            'execution_events',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('case_id', sa.Integer(), nullable=False),
            sa.Column('event_type', sa.String(50), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('metadata', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['case_id'], ['execution_cases.id'], name='fk_events_cases'),
        )
    
    # Create execution_tasks
    if 'execution_tasks' not in table_names:
        op.create_table(
            'execution_tasks',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('case_id', sa.Integer(), nullable=False),
            sa.Column('task_type', sa.String(100), nullable=False),
            sa.Column('instruction', sa.Text(), nullable=True),
            sa.Column('priority', sa.String(20), nullable=False, server_default='medium'),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
            sa.Column('assigned_to', sa.String(100), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['case_id'], ['execution_cases.id'], name='fk_tasks_cases'),
        )
    
    # Create execution_assessments
    if 'execution_assessments' not in table_names:
        op.create_table(
            'execution_assessments',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('case_id', sa.Integer(), nullable=False),
            sa.Column('classification', sa.String(50), nullable=False),
            sa.Column('estimated_value', sa.Integer(), nullable=True),
            sa.Column('estimated_profit', sa.Integer(), nullable=True),
            sa.Column('confidence_score', sa.Float(), nullable=True),
            sa.Column('risk_score', sa.Float(), nullable=True),
            sa.Column('strategy', sa.String(100), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['case_id'], ['execution_cases.id'], name='fk_assessments_cases'),
        )


def downgrade() -> None:
    """Drop remaining execution tables"""
    op.drop_table('execution_assessments', if_exists=True)
    op.drop_table('execution_tasks', if_exists=True)
    op.drop_table('execution_events', if_exists=True)
