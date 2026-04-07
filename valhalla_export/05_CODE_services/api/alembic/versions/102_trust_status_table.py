"""Pack 104: add trust_status table

Revision ID: 102_trust_status_table
Revises: 101_bahamas_plans_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "102_trust_status_table"
down_revision = "101_bahamas_plans_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "trust_status" not in inspect(bind).get_table_names():
        op.create_table(
            "trust_status",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("trust_code", sa.String(), nullable=False),
            sa.Column("display_name", sa.String(), nullable=False),
            sa.Column("lawyer_engaged", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("draft_complete", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("signed", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("bank_accounts_open", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("life_policies_assigned", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("property_titled", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("status", sa.String(), server_default=sa.text("'pending'")),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("trust_status")
