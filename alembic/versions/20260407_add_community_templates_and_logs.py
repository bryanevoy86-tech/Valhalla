"""add community templates and message logs

Revision ID: add_community_templates_and_logs_20260407
Revises: None
Create Date: 2026-04-07

Add tables for community templates and message audit logging.
These tables are independent of other migrations and can be applied standalone.
"""

from alembic import op
import sqlalchemy as sa


revision = "add_community_templates_and_logs_20260407"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "community_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
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
    )
    op.create_index("ix_community_templates_name", "community_templates", ["name"])
    op.create_index("ix_community_templates_template_type", "community_templates", ["template_type"])
    op.create_index("ix_community_templates_channel", "community_templates", ["channel"])
    op.create_index("ix_community_templates_audience_type", "community_templates", ["audience_type"])
    op.create_index("ix_community_templates_region", "community_templates", ["region"])
    op.create_index("ix_community_templates_status", "community_templates", ["status"])
    op.create_index("ix_community_templates_approval_status", "community_templates", ["approval_status"])

    op.create_table(
        "community_message_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contact_id", sa.Integer(), sa.ForeignKey("community_contacts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("community_templates.id", ondelete="SET NULL"), nullable=True),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("direction", sa.String(length=50), nullable=False, server_default="outbound"),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("delivery_status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("block_reason", sa.Text(), nullable=True),
        sa.Column("sent_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_community_message_logs_contact_id", "community_message_logs", ["contact_id"])
    op.create_index("ix_community_message_logs_template_id", "community_message_logs", ["template_id"])
    op.create_index("ix_community_message_logs_channel", "community_message_logs", ["channel"])
    op.create_index("ix_community_message_logs_delivery_status", "community_message_logs", ["delivery_status"])


def downgrade():
    op.drop_index("ix_community_message_logs_delivery_status", table_name="community_message_logs")
    op.drop_index("ix_community_message_logs_channel", table_name="community_message_logs")
    op.drop_index("ix_community_message_logs_template_id", table_name="community_message_logs")
    op.drop_index("ix_community_message_logs_contact_id", table_name="community_message_logs")
    op.drop_table("community_message_logs")

    op.drop_index("ix_community_templates_approval_status", table_name="community_templates")
    op.drop_index("ix_community_templates_status", table_name="community_templates")
    op.drop_index("ix_community_templates_region", table_name="community_templates")
    op.drop_index("ix_community_templates_audience_type", table_name="community_templates")
    op.drop_index("ix_community_templates_channel", table_name="community_templates")
    op.drop_index("ix_community_templates_template_type", table_name="community_templates")
    op.drop_index("ix_community_templates_name", table_name="community_templates")
    op.drop_table("community_templates")
