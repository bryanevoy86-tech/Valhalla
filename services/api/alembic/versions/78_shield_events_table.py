"""add shield events table

Revision ID: 78_shield_events_table
Revises: 77_legacies_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa

revision = "78_shield_events_table"
down_revision = "77_legacies_table"
branch_labels = None
depends_on = None

def _table_exists(name: str, schema: str | None = None) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)

def upgrade():
    if not _table_exists("shield_events"):
        op.create_table(
            "shield_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), server_default="low"),
        sa.Column("description", sa.String()),
        sa.Column("resolved", sa.String(), server_default="pending"),
        sa.Column("created_at", sa.DateTime())
        )

def downgrade():
    op.drop_table("shield_events")
