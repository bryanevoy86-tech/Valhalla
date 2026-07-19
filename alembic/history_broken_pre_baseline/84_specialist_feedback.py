"""create specialist_feedback table

Revision ID: 84_specialist_feedback
Revises: 83_god_cases
Create Date: 2025-11-21 00:05:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "84_specialist_feedback"
down_revision: Union[str, Sequence[str], None] = "83_god_cases"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str, schema: str | None = None) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)


def upgrade() -> None:
    if not _table_exists("specialist_feedback"):
        op.create_table(
            "specialist_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "god_case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("god_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("specialist_role", sa.String(length=50), nullable=False),
        sa.Column("specialist_name", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column(
            "suggested_changes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_specialist_feedback_case_id",
            "specialist_feedback",
            ["god_case_id"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index("ix_specialist_feedback_case_id", table_name="specialist_feedback")
    op.drop_table("specialist_feedback")
