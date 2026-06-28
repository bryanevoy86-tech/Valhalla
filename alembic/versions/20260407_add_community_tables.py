"""Add community management tables

Revision ID: 20260407_community_tables
Revises: 2e6ee01fce5e
Create Date: 2026-04-07

Creates complete community contact management schema:
- community_contacts (base)
- community_templates
- community_campaigns
- community_interactions (references contacts)
- community_tasks (references contacts)
- community_referrals (references contacts)
- community_reputation_events (references contacts)
- community_message_logs (references contacts)

Order: Creates community_contacts first, then dependent tables.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260407_community_tables"
down_revision = "2e6ee01fce5e"
branch_labels = None
depends_on = None


def upgrade():
    # STEP 1: Create community_contacts (base table - no FKs)
    op.create_table(
        "community_contacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("organization_name", sa.String(length=255), nullable=True),
        sa.Column("contact_type", sa.String(length=100), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("preferred_channel", sa.String(length=50), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("relationship_stage", sa.String(length=50), nullable=False, server_default="new"),
        sa.Column("trust_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("consent_email", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("consent_sms", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("owner_user_id", sa.String(length=100), nullable=True),
        sa.Column("last_contact_at", sa.DateTime(), nullable=True),
        sa.Column("next_follow_up_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_contacts_contact_type", "community_contacts", ["contact_type"])
    op.create_index("ix_community_contacts_region", "community_contacts", ["region"])
    op.create_index("ix_community_contacts_email", "community_contacts", ["email"])
    op.create_index("ix_community_contacts_relationship_stage", "community_contacts", ["relationship_stage"])
    op.create_index("ix_community_contacts_next_follow_up_at", "community_contacts", ["next_follow_up_at"])

    # STEP 2: Create community_templates (independent)
    op.create_table(
        "community_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("template_type", sa.String(length=100), nullable=False),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("audience_type", sa.String(length=100), nullable=True),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("approval_status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("approved_by", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_templates_name", "community_templates", ["name"])
    op.create_index("ix_community_templates_template_type", "community_templates", ["template_type"])
    op.create_index("ix_community_templates_channel", "community_templates", ["channel"])
    op.create_index("ix_community_templates_audience_type", "community_templates", ["audience_type"])
    op.create_index("ix_community_templates_region", "community_templates", ["region"])
    op.create_index("ix_community_templates_status", "community_templates", ["status"])
    op.create_index("ix_community_templates_approval_status", "community_templates", ["approval_status"])

    # STEP 3: Create community_campaigns (independent)
    op.create_table(
        "community_campaigns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("campaign_type", sa.String(length=100), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("audience_type", sa.String(length=100), nullable=False),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("budget", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("approval_status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("start_date", sa.DateTime(), nullable=True),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_campaigns_name", "community_campaigns", ["name"])
    op.create_index("ix_community_campaigns_campaign_type", "community_campaigns", ["campaign_type"])
    op.create_index("ix_community_campaigns_region", "community_campaigns", ["region"])
    op.create_index("ix_community_campaigns_status", "community_campaigns", ["status"])

    # STEP 4: Create community_interactions (references contacts & campaigns)
    op.create_table(
        "community_interactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=True),
        sa.Column("interaction_type", sa.String(length=100), nullable=False),
        sa.Column("direction", sa.String(length=50), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("outcome", sa.String(length=100), nullable=True),
        sa.Column("sentiment", sa.String(length=50), nullable=True),
        sa.Column("follow_up_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("follow_up_at", sa.DateTime(), nullable=True),
        sa.Column("performed_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["community_contacts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campaign_id"], ["community_campaigns.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_interactions_contact_id", "community_interactions", ["contact_id"])
    op.create_index("ix_community_interactions_campaign_id", "community_interactions", ["campaign_id"])
    op.create_index("ix_community_interactions_interaction_type", "community_interactions", ["interaction_type"])

    # STEP 5: Create community_tasks (references contacts & campaigns)
    op.create_table(
        "community_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("campaign_id", sa.Integer(), nullable=True),
        sa.Column("task_type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("priority", sa.String(length=50), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="open"),
        sa.Column("assigned_to", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["contact_id"], ["community_contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["campaign_id"], ["community_campaigns.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_tasks_contact_id", "community_tasks", ["contact_id"])
    op.create_index("ix_community_tasks_campaign_id", "community_tasks", ["campaign_id"])
    op.create_index("ix_community_tasks_due_at", "community_tasks", ["due_at"])
    op.create_index("ix_community_tasks_status", "community_tasks", ["status"])

    # STEP 6: Create community_referrals (references contacts)
    op.create_table(
        "community_referrals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_contact_id", sa.Integer(), nullable=True),
        sa.Column("referred_contact_id", sa.Integer(), nullable=True),
        sa.Column("referral_type", sa.String(length=100), nullable=False),
        sa.Column("referral_status", sa.String(length=50), nullable=False, server_default="new"),
        sa.Column("estimated_value", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["source_contact_id"], ["community_contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["referred_contact_id"], ["community_contacts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_referrals_source_contact_id", "community_referrals", ["source_contact_id"])
    op.create_index("ix_community_referrals_referred_contact_id", "community_referrals", ["referred_contact_id"])
    op.create_index("ix_community_referrals_referral_status", "community_referrals", ["referral_status"])

    # STEP 7: Create community_reputation_events (references contacts)
    op.create_table(
        "community_reputation_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("score_delta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["community_contacts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_reputation_events_contact_id", "community_reputation_events", ["contact_id"])
    op.create_index("ix_community_reputation_events_event_type", "community_reputation_events", ["event_type"])

    # STEP 8: Create community_message_logs (references contacts & templates)
    op.create_table(
        "community_message_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("template_id", sa.Integer(), nullable=True),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("direction", sa.String(length=50), nullable=False, server_default="outbound"),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("delivery_status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("block_reason", sa.Text(), nullable=True),
        sa.Column("sent_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["contact_id"], ["community_contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["template_id"], ["community_templates.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_message_logs_contact_id", "community_message_logs", ["contact_id"])
    op.create_index("ix_community_message_logs_template_id", "community_message_logs", ["template_id"])
    op.create_index("ix_community_message_logs_channel", "community_message_logs", ["channel"])
    op.create_index("ix_community_message_logs_delivery_status", "community_message_logs", ["delivery_status"])


def downgrade():
    # Drop in reverse order of creation
    op.drop_index("ix_community_message_logs_delivery_status", table_name="community_message_logs")
    op.drop_index("ix_community_message_logs_channel", table_name="community_message_logs")
    op.drop_index("ix_community_message_logs_template_id", table_name="community_message_logs")
    op.drop_index("ix_community_message_logs_contact_id", table_name="community_message_logs")
    op.drop_table("community_message_logs")

    op.drop_index("ix_community_reputation_events_event_type", table_name="community_reputation_events")
    op.drop_index("ix_community_reputation_events_contact_id", table_name="community_reputation_events")
    op.drop_table("community_reputation_events")

    op.drop_index("ix_community_referrals_referral_status", table_name="community_referrals")
    op.drop_index("ix_community_referrals_referred_contact_id", table_name="community_referrals")
    op.drop_index("ix_community_referrals_source_contact_id", table_name="community_referrals")
    op.drop_table("community_referrals")

    op.drop_index("ix_community_tasks_status", table_name="community_tasks")
    op.drop_index("ix_community_tasks_due_at", table_name="community_tasks")
    op.drop_index("ix_community_tasks_campaign_id", table_name="community_tasks")
    op.drop_index("ix_community_tasks_contact_id", table_name="community_tasks")
    op.drop_table("community_tasks")

    op.drop_index("ix_community_interactions_interaction_type", table_name="community_interactions")
    op.drop_index("ix_community_interactions_campaign_id", table_name="community_interactions")
    op.drop_index("ix_community_interactions_contact_id", table_name="community_interactions")
    op.drop_table("community_interactions")

    op.drop_index("ix_community_campaigns_status", table_name="community_campaigns")
    op.drop_index("ix_community_campaigns_region", table_name="community_campaigns")
    op.drop_index("ix_community_campaigns_campaign_type", table_name="community_campaigns")
    op.drop_index("ix_community_campaigns_name", table_name="community_campaigns")
    op.drop_table("community_campaigns")

    op.drop_index("ix_community_templates_approval_status", table_name="community_templates")
    op.drop_index("ix_community_templates_status", table_name="community_templates")
    op.drop_index("ix_community_templates_region", table_name="community_templates")
    op.drop_index("ix_community_templates_audience_type", table_name="community_templates")
    op.drop_index("ix_community_templates_channel", table_name="community_templates")
    op.drop_index("ix_community_templates_template_type", table_name="community_templates")
    op.drop_index("ix_community_templates_name", table_name="community_templates")
    op.drop_table("community_templates")

    op.drop_index("ix_community_contacts_next_follow_up_at", table_name="community_contacts")
    op.drop_index("ix_community_contacts_relationship_stage", table_name="community_contacts")
    op.drop_index("ix_community_contacts_email", table_name="community_contacts")
    op.drop_index("ix_community_contacts_region", table_name="community_contacts")
    op.drop_index("ix_community_contacts_contact_type", table_name="community_contacts")
    op.drop_table("community_contacts")
