"""Fix and complete community management schema

Revision ID: 20260408_community_schema_fix
Revises: 0077
Create Date: 2026-04-08

Ensures all community tables exist with correct dependencies:
- Handles orphaned/partial migrations
- Idempotent: safe to run multiple times
- Creates missing tables only
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260408_community_schema_fix'
down_revision = '2e6ee01fce5e'
branch_labels = None
depends_on = None


def _table_exists(bind, table_name: str) -> bool:
    """Check if a table exists in the current database."""
    try:
        inspector = inspect(bind)
        return table_name in inspector.get_table_names()
    except Exception:
        return False


def upgrade():
    bind = op.get_bind()
    
    # STEP 1: Ensure community_contacts (base table - no FKs)
    if not _table_exists(bind, 'community_contacts'):
        op.create_table(
            'community_contacts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('full_name', sa.String(length=255), nullable=False),
            sa.Column('organization_name', sa.String(length=255), nullable=True),
            sa.Column('contact_type', sa.String(length=100), nullable=False),
            sa.Column('region', sa.String(length=100), nullable=True),
            sa.Column('phone', sa.String(length=50), nullable=True),
            sa.Column('email', sa.String(length=255), nullable=True),
            sa.Column('preferred_channel', sa.String(length=50), nullable=True),
            sa.Column('source', sa.String(length=100), nullable=True),
            sa.Column('tags', sa.Text(), nullable=True),
            sa.Column('relationship_stage', sa.String(length=50), nullable=False, server_default='new'),
            sa.Column('trust_score', sa.Integer(), nullable=False, server_default='50'),
            sa.Column('consent_email', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('consent_sms', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('owner_user_id', sa.String(length=100), nullable=True),
            sa.Column('last_contact_at', sa.DateTime(), nullable=True),
            sa.Column('next_follow_up_at', sa.DateTime(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_community_contacts_contact_type', 'community_contacts', ['contact_type'])
        op.create_index('ix_community_contacts_region', 'community_contacts', ['region'])
        op.create_index('ix_community_contacts_email', 'community_contacts', ['email'])
        op.create_index('ix_community_contacts_relationship_stage', 'community_contacts', ['relationship_stage'])
        op.create_index('ix_community_contacts_next_follow_up_at', 'community_contacts', ['next_follow_up_at'])

    # STEP 2: Ensure community_templates (independent)
    if not _table_exists(bind, 'community_templates'):
        op.create_table(
            'community_templates',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('template_type', sa.String(length=100), nullable=False),
            sa.Column('channel', sa.String(length=50), nullable=False),
            sa.Column('audience_type', sa.String(length=100), nullable=True),
            sa.Column('region', sa.String(length=100), nullable=True),
            sa.Column('subject', sa.String(length=255), nullable=True),
            sa.Column('body', sa.Text(), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
            sa.Column('approval_status', sa.String(length=50), nullable=False, server_default='draft'),
            sa.Column('created_by', sa.String(length=100), nullable=True),
            sa.Column('approved_by', sa.String(length=100), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_community_templates_name', 'community_templates', ['name'])
        op.create_index('ix_community_templates_template_type', 'community_templates', ['template_type'])
        op.create_index('ix_community_templates_channel', 'community_templates', ['channel'])

    # STEP 3: Ensure community_campaigns (independent)
    if not _table_exists(bind, 'community_campaigns'):
        op.create_table(
            'community_campaigns',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('campaign_type', sa.String(length=100), nullable=False),
            sa.Column('region', sa.String(length=100), nullable=True),
            sa.Column('audience_type', sa.String(length=100), nullable=False),
            sa.Column('objective', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
            sa.Column('budget', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('start_date', sa.Date(), nullable=True),
            sa.Column('end_date', sa.Date(), nullable=True),
            sa.Column('created_by', sa.String(length=100), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_community_campaigns_name', 'community_campaigns', ['name'])

    # STEP 4: Ensure community_interactions (depends on contacts + campaigns)
    if not _table_exists(bind, 'community_interactions'):
        op.create_table(
            'community_interactions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('contact_id', sa.Integer(), nullable=False),
            sa.Column('campaign_id', sa.Integer(), nullable=True),
            sa.Column('interaction_type', sa.String(length=100), nullable=False),
            sa.Column('channel', sa.String(length=50), nullable=False),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('outcome', sa.String(length=100), nullable=True),
            sa.Column('value_impact', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['contact_id'], ['community_contacts.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['campaign_id'], ['community_campaigns.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_community_interactions_contact_id', 'community_interactions', ['contact_id'])
        op.create_index('ix_community_interactions_campaign_id', 'community_interactions', ['campaign_id'])

    # STEP 5: Ensure community_tasks
    if not _table_exists(bind, 'community_tasks'):
        op.create_table(
            'community_tasks',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('contact_id', sa.Integer(), nullable=False),
            sa.Column('campaign_id', sa.Integer(), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='open'),
            sa.Column('priority', sa.String(length=50), nullable=False, server_default='medium'),
            sa.Column('assigned_to', sa.String(length=100), nullable=True),
            sa.Column('due_date', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['contact_id'], ['community_contacts.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['campaign_id'], ['community_campaigns.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_community_tasks_contact_id', 'community_tasks', ['contact_id'])
        op.create_index('ix_community_tasks_status', 'community_tasks', ['status'])

    # STEP 6: Ensure community_referrals
    if not _table_exists(bind, 'community_referrals'):
        op.create_table(
            'community_referrals',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('source_contact_id', sa.Integer(), nullable=False),
            sa.Column('referred_contact_id', sa.Integer(), nullable=False),
            sa.Column('relationship', sa.String(length=100), nullable=True),
            sa.Column('referral_date', sa.DateTime(), nullable=False),
            sa.Column('conversion_status', sa.String(length=50), nullable=False, server_default='pending'),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['source_contact_id'], ['community_contacts.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['referred_contact_id'], ['community_contacts.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_community_referrals_source_contact_id', 'community_referrals', ['source_contact_id'])
        op.create_index('ix_community_referrals_referred_contact_id', 'community_referrals', ['referred_contact_id'])

    # STEP 7: Ensure community_reputation_events
    if not _table_exists(bind, 'community_reputation_events'):
        op.create_table(
            'community_reputation_events',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('contact_id', sa.Integer(), nullable=False),
            sa.Column('event_type', sa.String(length=100), nullable=False),
            sa.Column('value_change', sa.Integer(), nullable=False),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['contact_id'], ['community_contacts.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_community_reputation_events_contact_id', 'community_reputation_events', ['contact_id'])
        op.create_index('ix_community_reputation_events_event_type', 'community_reputation_events', ['event_type'])

    # STEP 8: Ensure community_message_logs (depends on contacts + templates)
    if not _table_exists(bind, 'community_message_logs'):
        op.create_table(
            'community_message_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('contact_id', sa.Integer(), nullable=True),
            sa.Column('template_id', sa.Integer(), nullable=True),
            sa.Column('channel', sa.String(length=50), nullable=False),
            sa.Column('direction', sa.String(length=50), nullable=False, server_default='outbound'),
            sa.Column('subject', sa.String(length=255), nullable=True),
            sa.Column('body', sa.Text(), nullable=False),
            sa.Column('delivery_status', sa.String(length=50), nullable=False, server_default='draft'),
            sa.Column('block_reason', sa.Text(), nullable=True),
            sa.Column('sent_by', sa.String(length=100), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('sent_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['contact_id'], ['community_contacts.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['template_id'], ['community_templates.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_community_message_logs_contact_id', 'community_message_logs', ['contact_id'])
        op.create_index('ix_community_message_logs_template_id', 'community_message_logs', ['template_id'])


def downgrade():
    """Downgrade by dropping community tables"""
    op.drop_table('community_message_logs')
    op.drop_table('community_reputation_events')
    op.drop_table('community_referrals')
    op.drop_table('community_tasks')
    op.drop_table('community_interactions')
    op.drop_table('community_campaigns')
    op.drop_table('community_templates')
    op.drop_table('community_contacts')
