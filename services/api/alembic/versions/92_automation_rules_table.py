"""Pack 93: add automation_rules table (renumbered in chain)

Revision ID: 92_automation_rules_table
Revises: 91_notifications_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "92_automation_rules_table"
down_revision = "91_notifications_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "automation_rules" not in inspect(bind).get_table_names():
        op.create_table(
            "automation_rules",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("category", sa.String(), server_default=sa.text("'general'")),
            sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("trigger_expression", sa.Text(), nullable=False),
            sa.Column("action_expression", sa.Text(), nullable=False),
            sa.Column("description", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("automation_rules")
