"""create god_cases table

Revision ID: 83_god_cases
Revises: 4cd55687949f
Create Date: 2025-11-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "83_god_cases"
down_revision: Union[str, Sequence[str], None] = "4cd55687949f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "god_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("heimdall_output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("loki_output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("arbitration_output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("needs_rescan", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_god_cases_id", "god_cases", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_god_cases_id", table_name="god_cases")
    op.drop_table("god_cases")
