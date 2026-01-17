"""add underwriter assessments table

Revision ID: 80_underwriter_assessments_table
Revises: 79_legal_profiles_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa

revision = "80_underwriter_assessments_table"
down_revision = "79_legal_profiles_table"
branch_labels = None
depends_on = None

def _table_exists(name: str, schema: str | None = None) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)

def upgrade():
    if not _table_exists("underwriter_assessments"):
        op.create_table(
            "underwriter_assessments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("deal_id", sa.Integer(), nullable=False),
        sa.Column("risk_score", sa.Float(), server_default="0.0"),
        sa.Column("legal_risk_score", sa.Float(), server_default="0.0"),
        sa.Column("profitability_score", sa.Float(), server_default="0.0"),
        sa.Column("decision", sa.String(), server_default="review"),
        sa.Column("notes", sa.String()),
        sa.Column("country", sa.String()),
        sa.Column("region", sa.String()),
        sa.Column("legal_profile_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime()),
        )

def downgrade():
    op.drop_table("underwriter_assessments")
