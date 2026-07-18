"""add god verdicts

Revision ID: ea0ce6b7a331
Revises: bda88eb16728
Create Date: 2025-11-21 13:18:24.501994

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'ea0ce6b7a331'
down_revision: Union[str, Sequence[str], None] = 'bda88eb16728'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str, schema: str | None = None) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)


def upgrade() -> None:
    """Upgrade schema."""
    if not _table_exists("god_verdicts"):
        op.create_table(
            "god_verdicts",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("trigger", sa.String(length=50), nullable=True),
            sa.Column("heimdall_summary", sa.Text(), nullable=True),
            sa.Column("heimdall_recommendation", postgresql.JSONB, nullable=True),
            sa.Column("heimdall_confidence", sa.String(length=20), nullable=True),
            sa.Column("loki_summary", sa.Text(), nullable=True),
            sa.Column("loki_recommendation", postgresql.JSONB, nullable=True),
            sa.Column("loki_confidence", sa.String(length=20), nullable=True),
            sa.Column("consensus", sa.String(length=20), nullable=True),
            sa.Column("risk_level", sa.String(length=20), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("metadata", postgresql.JSONB, nullable=True),
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("god_verdicts")
