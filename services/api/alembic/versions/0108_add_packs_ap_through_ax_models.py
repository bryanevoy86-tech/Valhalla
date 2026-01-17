"""Add PACKS AP through AX models

Revision ID: 0108
Revises: 0107_alter_contract_records_schema
Create Date: 2025-12-05 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0108'
down_revision = '0107_alter_contract_records_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PACK AP: Decision Governance
    op.create_table(
        'decision_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('allowed_roles', sa.String(), nullable=True),
        sa.Column('min_approvals', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index('ix_decision_policies_id', 'decision_policies', ['id'])
    op.create_index('ix_decision_policies_key', 'decision_policies', ['key'])

    op.create_table(
        'decision_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('policy_key', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('initiator', sa.String(), nullable=False),
        sa.Column('initiator_role', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_decision_records_id', 'decision_records', ['id'])
    op.create_index('ix_decision_records_policy_key', 'decision_records', ['policy_key'])

    # PACK AQ: Workflow Guardrails
    op.create_table(
        'workflow_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('is_allowed', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workflow_rules_id', 'workflow_rules', ['id'])

    op.create_table(
        'workflow_violations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('violation_reason', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workflow_violations_id', 'workflow_violations', ['id'])

    # PACK AR: Heimdall Workload
    op.create_table(
        'heimdall_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('priority', sa.String(), nullable=False, server_default='normal'),
        sa.Column('status', sa.String(), nullable=False, server_default='queued'),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_heimdall_jobs_id', 'heimdall_jobs', ['id'])
    op.create_index('ix_heimdall_jobs_status', 'heimdall_jobs', ['status'])

    op.create_table(
        'heimdall_workload_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('max_concurrent', sa.Integer(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_type')
    )
    op.create_index('ix_heimdall_workload_config_id', 'heimdall_workload_config', ['id'])

    # PACK AS: Empire Journal Engine
    op.create_table(
        'journal_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('tags', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_journal_entries_id', 'journal_entries', ['id'])

    # PACK AT: User Summary Snapshots
    op.create_table(
        'user_summary_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('summary_type', sa.String(), nullable=False, server_default='custom'),
        sa.Column('audience', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_summary_snapshots_id', 'user_summary_snapshots', ['id'])

    # PACK AU: Trust & Residency Profiles
    op.create_table(
        'trust_residency_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subject_type', sa.String(), nullable=False),
        sa.Column('subject_id', sa.String(), nullable=False),
        sa.Column('jurisdiction', sa.String(), nullable=True),
        sa.Column('trust_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('footprint_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trust_residency_profiles_id', 'trust_residency_profiles', ['id'])

    # PACK AV: Story Mode Engine
    op.create_table(
        'story_prompts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('audience', sa.String(), nullable=True),
        sa.Column('theme', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('prompt_text', sa.Text(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_story_prompts_id', 'story_prompts', ['id'])

    op.create_table(
        'story_outputs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prompt_id', sa.Integer(), nullable=True),
        sa.Column('audience', sa.String(), nullable=True),
        sa.Column('theme', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_story_outputs_id', 'story_outputs', ['id'])

    # PACK AW: Entity Links / Relationship Graph
    op.create_table(
        'entity_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_type', sa.String(), nullable=False),
        sa.Column('from_id', sa.String(), nullable=False),
        sa.Column('to_type', sa.String(), nullable=False),
        sa.Column('to_id', sa.String(), nullable=False),
        sa.Column('rel_type', sa.String(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_entity_links_id', 'entity_links', ['id'])
    op.create_index('ix_entity_links_from', 'entity_links', ['from_type', 'from_id'])
    op.create_index('ix_entity_links_to', 'entity_links', ['to_type', 'to_id'])

    # PACK AX: Feature Flags & Experiments
    op.create_table(
        'feature_flags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('audience', sa.String(), nullable=True),
        sa.Column('variant', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index('ix_feature_flags_id', 'feature_flags', ['id'])

    # Supporting models
    op.create_table(
        'children_hub',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_children_hub_id', 'children_hub', ['id'])

    op.create_table(
        'freeze_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deal_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('event_date', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_freeze_events_id', 'freeze_events', ['id'])


def downgrade() -> None:
    # PACK AX
    op.drop_table('feature_flags')

    # PACK AW
    op.drop_table('entity_links')

    # PACK AV
    op.drop_table('story_outputs')
    op.drop_table('story_prompts')

    # PACK AU
    op.drop_table('trust_residency_profiles')

    # PACK AT
    op.drop_table('user_summary_snapshots')

    # PACK AS
    op.drop_table('journal_entries')

    # PACK AR
    op.drop_table('heimdall_workload_config')
    op.drop_table('heimdall_jobs')

    # PACK AQ
    op.drop_table('workflow_violations')
    op.drop_table('workflow_rules')

    # PACK AP
    op.drop_table('decision_records')
    op.drop_table('decision_policies')

    # Supporting
    op.drop_table('freeze_events')
    op.drop_table('children_hub')
