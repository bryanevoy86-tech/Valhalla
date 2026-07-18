"""Pack 92: add notifications table (renumbered in chain)

Revision ID: 91_notifications_table
Revises: 90_empire_snapshots_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "91_notifications_table"
down_revision = "90_empire_snapshots_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "notifications" not in inspect(bind).get_table_names():
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("channel", sa.String(), server_default=sa.text("'system'")),
            sa.Column("audience", sa.String(), server_default=sa.text("'king'")),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("severity", sa.String(), server_default=sa.text("'info'")),
            sa.Column("read", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("read_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("notifications")
