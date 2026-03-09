"""add disputes

Revision ID: 4cd55687949f
Revises: ea0ce6b7a331
Create Date: 2025-11-21 13:20:01.841528

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4cd55687949f'
down_revision: Union[str, Sequence[str], None] = 'ea0ce6b7a331'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str, schema: str | None = None) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)


def upgrade() -> None:
    """Upgrade schema."""
    if not _table_exists("disputes"):
        op.create_table(
            "disputes",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("human_role", sa.String(length=30), nullable=True),
            sa.Column("human_specialist_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("topic", sa.String(length=200), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("human_position", postgresql.JSONB, nullable=True),
            sa.Column("heimdall_position", postgresql.JSONB, nullable=True),
            sa.Column("loki_position", postgresql.JSONB, nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
            sa.Column("resolution_summary", sa.Text(), nullable=True),
            sa.Column("resolution_metadata", postgresql.JSONB, nullable=True),
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("disputes")
