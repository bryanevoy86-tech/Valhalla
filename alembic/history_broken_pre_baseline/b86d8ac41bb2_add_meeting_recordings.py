"""add meeting recordings

Revision ID: b86d8ac41bb2
Revises: f8dc20521d28
Create Date: 2025-11-21 13:06:39.213157

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b86d8ac41bb2'
down_revision: Union[str, Sequence[str], None] = 'f8dc20521d28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str, schema: str | None = None) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)


def upgrade() -> None:
    """Upgrade schema."""
    if not _table_exists("meeting_recordings"):
        op.create_table(
            "meeting_recordings",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("source", sa.String(length=50), nullable=False),
            sa.Column("external_id", sa.String(length=200), nullable=True),
            sa.Column("title", sa.String(length=200), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("participants", postgresql.JSONB, nullable=True),
            sa.Column("raw_transcript", sa.Text(), nullable=True),
            sa.Column("transcript_json", postgresql.JSONB, nullable=True),
            sa.Column("tags", postgresql.JSONB, nullable=True),
            sa.Column("related_case_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("metadata", postgresql.JSONB, nullable=True),
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("meeting_recordings")
