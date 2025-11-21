"""add tax opinions

Revision ID: bda88eb16728
Revises: b86d8ac41bb2
Create Date: 2025-11-21 13:08:10.201498

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'bda88eb16728'
down_revision: Union[str, Sequence[str], None] = 'b86d8ac41bb2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "tax_opinions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("jurisdiction", sa.String(length=20), nullable=False),
        sa.Column("tax_year", sa.String(length=10), nullable=True),
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.Column("specialist_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column("risk_level", sa.String(length=20), nullable=True),
        sa.Column("flags", postgresql.JSONB, nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("tax_opinions")
