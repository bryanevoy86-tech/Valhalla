"""Add PACKS SP, SQ, SO models

Revision ID: 0114
Revises: 0067
Create Date: 2025-01-07 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0114'
down_revision = 'pack_core_prelaunch_01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PACK SP: Life Event & Crisis Management Engine
    op.create_table(
        'crisis_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('crisis_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('triggers', sa.JSON(), nullable=True),
        sa.Column('severity_levels', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('crisis_id', name='uq_crisis_profiles_crisis_id')
    )
    op.create_index('ix_crisis_profiles_category', 'crisis_profiles', ['category'])

    op.create_table(
        'crisis_action_steps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('step_id', sa.String(255), nullable=False),
        sa.Column('crisis_id', sa.Integer(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('responsible_role', sa.String(100), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['crisis_id'], ['crisis_profiles.id'], ),
        sa.UniqueConstraint('step_id', name='uq_crisis_action_steps_step_id')
    )
    op.create_index('ix_crisis_action_steps_crisis_id', 'crisis_action_steps', ['crisis_id'])
    op.create_index('ix_crisis_action_steps_order', 'crisis_action_steps', ['order'])

    op.create_table(
        'crisis_log_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('log_id', sa.String(255), nullable=False),
        sa.Column('crisis_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('event', sa.Text(), nullable=False),
        sa.Column('actions_taken', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['crisis_id'], ['crisis_profiles.id'], ),
        sa.UniqueConstraint('log_id', name='uq_crisis_log_entries_log_id')
    )
    op.create_index('ix_crisis_log_entries_crisis_id', 'crisis_log_entries', ['crisis_id'])
    op.create_index('ix_crisis_log_entries_date', 'crisis_log_entries', ['date'])
    op.create_index('ix_crisis_log_entries_status', 'crisis_log_entries', ['status'])

    op.create_table(
        'crisis_workflows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.String(255), nullable=False),
        sa.Column('crisis_id', sa.String(255), nullable=False),
        sa.Column('current_step', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='intake'),
        sa.Column('triggered_date', sa.DateTime(), nullable=True),
        sa.Column('steps_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workflow_id', name='uq_crisis_workflows_workflow_id')
    )
    op.create_index('ix_crisis_workflows_status', 'crisis_workflows', ['status'])

    # PACK SQ: Partner / Marriage Stability Ops Module
    op.create_table(
        'relationship_ops_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profile_id', sa.String(255), nullable=False),
        sa.Column('partner_name', sa.String(255), nullable=False),
        sa.Column('shared_domains', sa.JSON(), nullable=True),
        sa.Column('communication_protocol', sa.JSON(), nullable=True),
        sa.Column('boundaries', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('profile_id', name='uq_relationship_ops_profiles_profile_id')
    )
    op.create_index('ix_relationship_ops_profiles_partner_name', 'relationship_ops_profiles', ['partner_name'])

    op.create_table(
        'coparenting_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.String(255), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('days', sa.JSON(), nullable=True),
        sa.Column('special_rules', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['profile_id'], ['relationship_ops_profiles.id'], ),
        sa.UniqueConstraint('schedule_id', name='uq_coparenting_schedules_schedule_id')
    )
    op.create_index('ix_coparenting_schedules_profile_id', 'coparenting_schedules', ['profile_id'])

    op.create_table(
        'household_responsibilities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(255), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('task', sa.String(255), nullable=False),
        sa.Column('frequency', sa.String(50), nullable=False),
        sa.Column('primary_responsible', sa.String(255), nullable=False),
        sa.Column('fallback_responsible', sa.String(255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['profile_id'], ['relationship_ops_profiles.id'], ),
        sa.UniqueConstraint('task_id', name='uq_household_responsibilities_task_id')
    )
    op.create_index('ix_household_responsibilities_profile_id', 'household_responsibilities', ['profile_id'])
    op.create_index('ix_household_responsibilities_frequency', 'household_responsibilities', ['frequency'])

    op.create_table(
        'communication_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('log_id', sa.String(255), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('topic', sa.String(255), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('follow_up_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['profile_id'], ['relationship_ops_profiles.id'], ),
        sa.UniqueConstraint('log_id', name='uq_communication_logs_log_id')
    )
    op.create_index('ix_communication_logs_profile_id', 'communication_logs', ['profile_id'])
    op.create_index('ix_communication_logs_date', 'communication_logs', ['date'])

    # PACK SO Legacy: Long-Term Legacy & Succession Archive Engine
    op.create_table(
        'legacy_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('legacy_id', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('long_term_goals', sa.JSON(), nullable=True),
        sa.Column('knowledge_domains', sa.JSON(), nullable=True),
        sa.Column('heir_candidates', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('legacy_id', name='uq_legacy_profiles_legacy_id')
    )
    op.create_index('ix_legacy_profiles_legacy_id', 'legacy_profiles', ['legacy_id'])

    op.create_table(
        'knowledge_packages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('package_id', sa.String(255), nullable=False),
        sa.Column('legacy_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['legacy_id'], ['legacy_profiles.id'], ),
        sa.UniqueConstraint('package_id', name='uq_knowledge_packages_package_id')
    )
    op.create_index('ix_knowledge_packages_legacy_id', 'knowledge_packages', ['legacy_id'])
    op.create_index('ix_knowledge_packages_category', 'knowledge_packages', ['category'])

    op.create_table(
        'succession_stages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stage_id', sa.String(255), nullable=False),
        sa.Column('legacy_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('trigger', sa.String(255), nullable=True),
        sa.Column('access_level', sa.JSON(), nullable=True),
        sa.Column('training_requirements', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['legacy_id'], ['legacy_profiles.id'], ),
        sa.UniqueConstraint('stage_id', name='uq_succession_stages_stage_id')
    )
    op.create_index('ix_succession_stages_legacy_id', 'succession_stages', ['legacy_id'])

    op.create_table(
        'legacy_vaults',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vault_id', sa.String(255), nullable=False),
        sa.Column('legacy_id', sa.Integer(), nullable=False),
        sa.Column('packages', sa.JSON(), nullable=True),
        sa.Column('successor_roles', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['legacy_id'], ['legacy_profiles.id'], ),
        sa.UniqueConstraint('vault_id', name='uq_legacy_vaults_vault_id')
    )
    op.create_index('ix_legacy_vaults_legacy_id', 'legacy_vaults', ['legacy_id'])


def downgrade() -> None:
    # Drop PACK SO Legacy tables
    op.drop_index('ix_legacy_vaults_legacy_id', table_name='legacy_vaults')
    op.drop_table('legacy_vaults')

    op.drop_index('ix_succession_stages_legacy_id', table_name='succession_stages')
    op.drop_table('succession_stages')

    op.drop_index('ix_knowledge_packages_category', table_name='knowledge_packages')
    op.drop_index('ix_knowledge_packages_legacy_id', table_name='knowledge_packages')
    op.drop_table('knowledge_packages')

    op.drop_index('ix_legacy_profiles_legacy_id', table_name='legacy_profiles')
    op.drop_table('legacy_profiles')

    # Drop PACK SQ tables
    op.drop_index('ix_communication_logs_date', table_name='communication_logs')
    op.drop_index('ix_communication_logs_profile_id', table_name='communication_logs')
    op.drop_table('communication_logs')

    op.drop_index('ix_household_responsibilities_frequency', table_name='household_responsibilities')
    op.drop_index('ix_household_responsibilities_profile_id', table_name='household_responsibilities')
    op.drop_table('household_responsibilities')

    op.drop_index('ix_coparenting_schedules_profile_id', table_name='coparenting_schedules')
    op.drop_table('coparenting_schedules')

    op.drop_index('ix_relationship_ops_profiles_partner_name', table_name='relationship_ops_profiles')
    op.drop_table('relationship_ops_profiles')

    # Drop PACK SP tables
    op.drop_index('ix_crisis_workflows_status', table_name='crisis_workflows')
    op.drop_table('crisis_workflows')

    op.drop_index('ix_crisis_log_entries_status', table_name='crisis_log_entries')
    op.drop_index('ix_crisis_log_entries_date', table_name='crisis_log_entries')
    op.drop_index('ix_crisis_log_entries_crisis_id', table_name='crisis_log_entries')
    op.drop_table('crisis_log_entries')

    op.drop_index('ix_crisis_action_steps_order', table_name='crisis_action_steps')
    op.drop_index('ix_crisis_action_steps_crisis_id', table_name='crisis_action_steps')
    op.drop_table('crisis_action_steps')

    op.drop_index('ix_crisis_profiles_category', table_name='crisis_profiles')
    op.drop_table('crisis_profiles')
