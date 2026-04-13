"""create remaining execution layer tables

Revision ID: 005_exec_remaining_tables
Revises: 004_exec_cases_only
Create Date: 2026-04-13 18:42:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_exec_remaining_tables'
down_revision = '004_exec_cases_only'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create remaining execution layer tables"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Create execution_events table
    if 'execution_events' not in inspector.get_table_names():
        op.create_table(
            'execution_events',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('case_id', sa.Integer(), nullable=False),
            sa.Column('event_type', sa.String(50), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('context_data', sa.Text(), nullable=True),
            sa.Column('actor', sa.String(100), nullable=False, server_default='system'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_foreign_key('fk_execution_events_case', 'execution_events', 'execution_cases', ['case_id'], ['id'])
    
    # Create execution_policies table
    if 'execution_policies' not in inspector.get_table_names():
        op.create_table(
            'execution_policies',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('policy_name', sa.String(100), nullable=False),
            sa.Column('policy_type', sa.String(50), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column('threshold_financial', sa.Float(), nullable=True),
            sa.Column('threshold_risk', sa.Float(), nullable=True),
            sa.Column('action_on_breach', sa.String(100), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
    
    # Create underwriter_assessments table
    if 'underwriter_assessments' not in inspector.get_table_names():
        op.create_table(
            'underwriter_assessments',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('estimated_arv', sa.Float(), nullable=False),
            sa.Column('estimated_repair_cost', sa.Float(), nullable=False),
            sa.Column('estimated_purchase_cost', sa.Float(), nullable=False),
            sa.Column('estimated_operating_cost', sa.Float(), nullable=False),
            sa.Column('estimated_profit', sa.Float(), nullable=False),
            sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0'),
            sa.Column('risk_score', sa.Float(), nullable=False, server_default='0'),
            sa.Column('confidence_level', sa.String(20), nullable=False, server_default='low'),
            sa.Column('safe_mode', sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column('blocked', sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
    
    # Create tasks table
    if 'tasks' not in inspector.get_table_names():
        op.create_table(
            'tasks',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('case_id', sa.Integer(), nullable=True),
            sa.Column('sequence', sa.Integer(), nullable=True),
            sa.Column('due_days', sa.Integer(), nullable=True),
            sa.Column('category', sa.String(), nullable=False, server_default='general'),
            sa.Column('assignee', sa.String(), nullable=False, server_default='king'),
            sa.Column('status', sa.String(), nullable=False, server_default='pending'),
            sa.Column('priority', sa.Integer(), nullable=False, server_default='5'),
            sa.Column('due_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_foreign_key('fk_tasks_case', 'tasks', 'execution_cases', ['case_id'], ['id'])


def downgrade() -> None:
    """Drop remaining execution layer tables"""
    op.drop_table('tasks', if_exists=True)
    op.drop_table('underwriter_assessments', if_exists=True)
    op.drop_table('execution_policies', if_exists=True)
    op.drop_table('execution_events', if_exists=True)
