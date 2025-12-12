"""add loki review tables

Revision ID: f358f8404d91
Revises: pack_65_buyer_match
Create Date: 2025-11-20 20:29:22.856323

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "f358f8404d91"
down_revision = "126_freeze_events_table"
branch_labels = None
depends_on = None


def _table_exists(name: str, schema: str | None = None) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)


def upgrade() -> None:
    if not _table_exists("loki_reviews"):
        op.create_table(
            "loki_reviews",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("input_source", sa.String(length=100), nullable=False),
            sa.Column("artifact_type", sa.String(length=100), nullable=False),
            sa.Column("risk_profile", sa.String(length=100), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("heimdall_reference_id", sa.String(length=100), nullable=True),
            sa.Column("human_reference_id", sa.String(length=100), nullable=True),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("result_severity", sa.String(length=20), nullable=True),
            sa.Column("raw_input", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("raw_output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )

    if not _table_exists("loki_findings"):
        op.create_table(
            "loki_findings",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "review_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("loki_reviews.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("category", sa.String(length=100), nullable=False),
            sa.Column("severity", sa.String(length=20), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("suggested_fix", sa.Text(), nullable=True),
            sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )


def downgrade() -> None:
    op.drop_table("loki_findings")
    op.drop_table("loki_reviews")
