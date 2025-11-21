"""add god sync records table

Revision ID: fa9eb99ebae2
Revises: 3e8296b25e8b
Create Date: 2025-11-21 00:43:51.833103

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'fa9eb99ebae2'
down_revision: Union[str, Sequence[str], None] = '3e8296b25e8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "god_sync_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("subject_type", sa.String(100), nullable=False),
        sa.Column("subject_reference", sa.String(200), nullable=True),
        sa.Column("heimdall_payload", postgresql.JSONB, nullable=True),
        sa.Column("loki_payload", postgresql.JSONB, nullable=True),
        sa.Column("sync_status", sa.String(20), nullable=False),
        sa.Column("conflict_summary", sa.Text, nullable=True),
        sa.Column("forwarded_case_id", postgresql.UUID(as_uuid=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("god_sync_records")
