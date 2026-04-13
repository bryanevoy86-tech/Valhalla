"""create execution layer tables

Revision ID: 002_exec_layer_tables
Revises: 001_exec_lead_intake
Create Date: 2026-04-13 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_exec_layer_tables'
down_revision = '001_exec_lead_intake'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create execution layer tables"""
    
    # Create execution_cases table
    op.create_table(
        'execution_cases',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('intake_id', sa.Integer(), nullable=False),
        sa.Column('assessment_id', sa.Integer(), nullable=True),
        sa.Column('case_type', sa.String(50), nullable=False, server_default='unknown'),
        sa.Column('route_target', sa.String(100), nullable=False, server_default=''),
        sa.Column('current_stage', sa.String(50), nullable=False, server_default='intake'),
        sa.Column('current_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('safe_mode', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('blocked', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('blocker_reason', sa.Text(), nullable=True),
        sa.Column('next_action', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(50), nullable=False, server_default='system'),
        sa.Column('updated_by', sa.String(50), nullable=False, server_default='system'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['intake_id'], ['lead_intake_exec.id']),
        sa.UniqueConstraint('intake_id'),
    )
    
    # Create execution_events table
    op.create_table(
        'execution_events',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('context_data', sa.Text(), nullable=True),
        sa.Column('actor', sa.String(100), nullable=False, server_default='system'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['case_id'], ['execution_cases.id']),
    )
    
    # Create execution_policies table
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
    
    # Create/update tasks table for execution workflows
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
        sa.ForeignKeyConstraint(['case_id'], ['execution_cases.id']),
    )


def downgrade() -> None:
    """Drop execution layer tables"""
    op.drop_table('tasks')
    op.drop_table('underwriter_assessments')
    op.drop_table('execution_policies')
    op.drop_table('execution_events')
    op.drop_table('execution_cases')

