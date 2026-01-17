"""add god review case models

Revision ID: 3e8296b25e8b
Revises: 107_system_health_reports_table
Create Date: 2025-11-20 22:45:06.123731

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "3e8296b25e8b"
down_revision = "0067"
branch_labels = None
depends_on = None


def _table_exists(name: str, schema: str | None = None) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)


def upgrade() -> None:
    if not _table_exists("god_review_cases"):
        op.create_table(
            "god_review_cases",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("subject_type", sa.String(length=100), nullable=False),
            sa.Column("subject_reference", sa.String(length=200), nullable=True),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("heimdall_summary", sa.Text(), nullable=True),
            sa.Column("loki_summary", sa.Text(), nullable=True),
            sa.Column("human_summary", sa.Text(), nullable=True),
            sa.Column("heimdall_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("loki_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("human_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("final_outcome", sa.String(length=30), nullable=False),
            sa.Column("final_notes", sa.Text(), nullable=True),
        )

    if not _table_exists("god_review_events"):
        op.create_table(
            "god_review_events",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "case_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("god_review_cases.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("actor", sa.String(length=30), nullable=False),
            sa.Column("event_type", sa.String(length=50), nullable=False),
            sa.Column("message", sa.Text(), nullable=True),
            sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )


def downgrade() -> None:
    op.drop_table("god_review_events")
    op.drop_table("god_review_cases")
