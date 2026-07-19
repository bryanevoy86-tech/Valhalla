"""add compliance signals table

Revision ID: 84_compliance_signals_table
Revises: 83_children_hub_tables
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa

revision = "84_compliance_signals_table"
down_revision = "83_children_hub_tables"
branch_labels = None
depends_on = None

def _table_exists(name: str, schema: str | None = None) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)

def upgrade():
    if not _table_exists("compliance_signals"):
        op.create_table(
            "compliance_signals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("deal_id", sa.Integer()),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), server_default="info"),
        sa.Column("code", sa.String()),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("score", sa.Float(), server_default="0.0"),
        sa.Column("created_at", sa.DateTime()),
        )

def downgrade():
    op.drop_table("compliance_signals")
