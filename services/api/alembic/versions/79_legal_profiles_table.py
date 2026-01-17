"""add legal profiles table

Revision ID: 79_legal_profiles_table
Revises: 78_shield_events_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa

revision = "79_legal_profiles_table"
down_revision = "78_shield_events_table"
branch_labels = None
depends_on = None

def _table_exists(name: str, schema: str | None = None) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)

def upgrade():
    if not _table_exists("legal_profiles"):
        op.create_table(
            "legal_profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("region", sa.String()),
        sa.Column("profile_name", sa.String(), nullable=False),
        sa.Column("category", sa.String()),
        sa.Column("risk_level", sa.String(), server_default="medium"),
        sa.Column("notes", sa.Text()),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
        )

def downgrade():
    op.drop_table("legal_profiles")
