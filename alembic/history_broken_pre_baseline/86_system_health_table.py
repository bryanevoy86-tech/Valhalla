"""Pack 86: add system_health table

Revision ID: 86_system_health_table
Revises: 85_integrity_events_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "86_system_health_table"
down_revision = "85_integrity_events_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "system_health" not in inspect(bind).get_table_names():
        op.create_table(
            "system_health",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("service_name", sa.String(), nullable=False, unique=True),
            sa.Column("status", sa.String(), server_default=sa.text("'unknown'")),
            sa.Column("last_heartbeat", sa.DateTime()),
            sa.Column("issue_count", sa.Integer(), server_default="0"),
            sa.Column("notes", sa.String()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("system_health")
