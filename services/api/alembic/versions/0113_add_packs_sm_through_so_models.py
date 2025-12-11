"""Add PACKS SM, SN, SO models

Revision ID: 0113
Revises: 0112
Create Date: 2025-01-07 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0113'
down_revision = '0112'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PACK SM: Kids Education & Development Engine
    op.create_table(
        'child_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('child_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('interests', sa.JSON(), nullable=True),
        sa.Column('skill_levels', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('child_id', name='uq_child_profiles_child_id')
    )
    op.create_index('ix_child_profiles_age', 'child_profiles', ['age'])

    op.create_table(
        'learning_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.String(255), nullable=False),
        sa.Column('child_id', sa.Integer(), nullable=False),
        sa.Column('timeframe', sa.String(50), nullable=False),
        sa.Column('goals', sa.JSON(), nullable=True),
        sa.Column('activities', sa.JSON(), nullable=True),
        sa.Column('parent_notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['child_id'], ['child_profiles.id'], ),
        sa.UniqueConstraint('plan_id', name='uq_learning_plans_plan_id')
    )
    op.create_index('ix_learning_plans_child_id', 'learning_plans', ['child_id'])
    op.create_index('ix_learning_plans_status', 'learning_plans', ['status'])

    op.create_table(
        'education_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('log_id', sa.String(255), nullable=False),
        sa.Column('child_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('completed_activities', sa.JSON(), nullable=True),
        sa.Column('highlights', sa.JSON(), nullable=True),
        sa.Column('parent_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['child_id'], ['child_profiles.id'], ),
        sa.UniqueConstraint('log_id', name='uq_education_logs_log_id')
    )
    op.create_index('ix_education_logs_child_id', 'education_logs', ['child_id'])
    op.create_index('ix_education_logs_date', 'education_logs', ['date'])

    op.create_table(
        'child_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('summary_id', sa.String(255), nullable=False),
        sa.Column('child_id', sa.Integer(), nullable=False),
        sa.Column('week_of', sa.DateTime(), nullable=False),
        sa.Column('completed_goals', sa.JSON(), nullable=True),
        sa.Column('fun_moments', sa.JSON(), nullable=True),
        sa.Column('growth_notes', sa.Text(), nullable=True),
        sa.Column('next_week_focus', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['child_id'], ['child_profiles.id'], ),
        sa.UniqueConstraint('summary_id', name='uq_child_summaries_summary_id')
    )
    op.create_index('ix_child_summaries_child_id', 'child_summaries', ['child_id'])
    op.create_index('ix_child_summaries_week_of', 'child_summaries', ['week_of'])

    # PACK SN: Mental Load Offloading Engine
    op.create_table(
        'mental_load_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entry_id', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('urgency_level', sa.Integer(), nullable=True),
        sa.Column('emotional_weight', sa.Integer(), nullable=True),
        sa.Column('action_required', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('cleared', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('cleared_date', sa.DateTime(), nullable=True),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entry_id', name='uq_mental_load_entries_entry_id')
    )
    op.create_index('ix_mental_load_entries_category', 'mental_load_entries', ['category'])
    op.create_index('ix_mental_load_entries_urgency', 'mental_load_entries', ['urgency_level'])
    op.create_index('ix_mental_load_entries_cleared', 'mental_load_entries', ['cleared'])

    op.create_table(
        'daily_load_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('summary_id', sa.String(255), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('total_items', sa.Integer(), nullable=False),
        sa.Column('urgent_items', sa.JSON(), nullable=True),
        sa.Column('action_items', sa.JSON(), nullable=True),
        sa.Column('delegated_items', sa.JSON(), nullable=True),
        sa.Column('cleared_items', sa.JSON(), nullable=True),
        sa.Column('waiting_items', sa.JSON(), nullable=True),
        sa.Column('parked_items', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('summary_id', name='uq_daily_load_summaries_summary_id')
    )
    op.create_index('ix_daily_load_summaries_date', 'daily_load_summaries', ['date'])

    op.create_table(
        'load_offload_workflows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.String(255), nullable=False),
        sa.Column('brain_dump', sa.Text(), nullable=True),
        sa.Column('processed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('categorized_items', sa.JSON(), nullable=True),
        sa.Column('workflow_stage', sa.String(50), nullable=False, server_default='intake'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workflow_id', name='uq_load_offload_workflows_workflow_id')
    )
    op.create_index('ix_load_offload_workflows_stage', 'load_offload_workflows', ['workflow_stage'])

    # PACK SO: Long-Term Empire Governance Map
    op.create_table(
        'empire_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('domain', sa.JSON(), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('responsibilities', sa.JSON(), nullable=True),
        sa.Column('authority_level', sa.Integer(), nullable=True),
        sa.Column('override_authority', sa.JSON(), nullable=True),
        sa.Column('override_by', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_id', name='uq_empire_roles_role_id')
    )
    op.create_index('ix_empire_roles_status', 'empire_roles', ['status'])
    op.create_index('ix_empire_roles_authority', 'empire_roles', ['authority_level'])

    op.create_table(
        'role_hierarchies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hierarchy_id', sa.String(255), nullable=False),
        sa.Column('superior_role_id', sa.String(255), nullable=False),
        sa.Column('subordinate_role_id', sa.String(255), nullable=False),
        sa.Column('override_rules', sa.Text(), nullable=True),
        sa.Column('escalation_path', sa.String(255), nullable=True),
        sa.Column('context', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hierarchy_id', name='uq_role_hierarchies_hierarchy_id')
    )
    op.create_index('ix_role_hierarchies_context', 'role_hierarchies', ['context'])

    op.create_table(
        'succession_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.String(255), nullable=False),
        sa.Column('triggered_role', sa.String(255), nullable=False),
        sa.Column('trigger_condition', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('fallback_roles', sa.JSON(), nullable=True),
        sa.Column('temporary_authority', sa.JSON(), nullable=True),
        sa.Column('documents_required', sa.JSON(), nullable=True),
        sa.Column('review_frequency', sa.String(50), nullable=True),
        sa.Column('last_reviewed', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan_id', name='uq_succession_plans_plan_id')
    )
    op.create_index('ix_succession_plans_triggered_role', 'succession_plans', ['triggered_role'])

    op.create_table(
        'empire_governance_maps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('map_id', sa.String(255), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('roles_count', sa.Integer(), nullable=False),
        sa.Column('role_graph', sa.JSON(), nullable=True),
        sa.Column('conflict_rules', sa.JSON(), nullable=True),
        sa.Column('escalation_rules', sa.JSON(), nullable=True),
        sa.Column('authority_matrix', sa.JSON(), nullable=True),
        sa.Column('risk_thresholds', sa.JSON(), nullable=True),
        sa.Column('automation_rules', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('map_id', name='uq_empire_governance_maps_map_id')
    )
    op.create_index('ix_empire_governance_maps_version', 'empire_governance_maps', ['version'])


def downgrade() -> None:
    # Drop PACK SO tables
    op.drop_index('ix_empire_governance_maps_version', table_name='empire_governance_maps')
    op.drop_table('empire_governance_maps')

    op.drop_index('ix_succession_plans_triggered_role', table_name='succession_plans')
    op.drop_table('succession_plans')

    op.drop_index('ix_role_hierarchies_context', table_name='role_hierarchies')
    op.drop_table('role_hierarchies')

    op.drop_index('ix_empire_roles_authority', table_name='empire_roles')
    op.drop_index('ix_empire_roles_status', table_name='empire_roles')
    op.drop_table('empire_roles')

    # Drop PACK SN tables
    op.drop_index('ix_load_offload_workflows_stage', table_name='load_offload_workflows')
    op.drop_table('load_offload_workflows')

    op.drop_index('ix_daily_load_summaries_date', table_name='daily_load_summaries')
    op.drop_table('daily_load_summaries')

    op.drop_index('ix_mental_load_entries_cleared', table_name='mental_load_entries')
    op.drop_index('ix_mental_load_entries_urgency', table_name='mental_load_entries')
    op.drop_index('ix_mental_load_entries_category', table_name='mental_load_entries')
    op.drop_table('mental_load_entries')

    # Drop PACK SM tables
    op.drop_index('ix_child_summaries_week_of', table_name='child_summaries')
    op.drop_index('ix_child_summaries_child_id', table_name='child_summaries')
    op.drop_table('child_summaries')

    op.drop_index('ix_education_logs_date', table_name='education_logs')
    op.drop_index('ix_education_logs_child_id', table_name='education_logs')
    op.drop_table('education_logs')

    op.drop_index('ix_learning_plans_status', table_name='learning_plans')
    op.drop_index('ix_learning_plans_child_id', table_name='learning_plans')
    op.drop_table('learning_plans')

    op.drop_index('ix_child_profiles_age', table_name='child_profiles')
    op.drop_table('child_profiles')
