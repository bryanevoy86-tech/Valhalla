"""
v3.5 - grants sources + records

Revision ID: v3_5_grants
Revises: v3_4_capital_telemetry
Create Date: 2025-11-02
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "v3_5_grants"
down_revision = "v3_4_capital_telemetry"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "grant_sources",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("region", sa.String(length=80), nullable=True),
        sa.Column("tags", sa.String(length=255), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_table(
        "grant_records",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("grant_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("program", sa.String(length=160), nullable=True),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("region", sa.String(length=80), nullable=True),
        sa.Column("amount_min", sa.Numeric(18, 2), nullable=True),
        sa.Column("amount_max", sa.Numeric(18, 2), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("link", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("score_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )


def downgrade():
    op.drop_table("grant_records")
    op.drop_table("grant_sources")
