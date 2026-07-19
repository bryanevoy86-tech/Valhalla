from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "83_god_cases"
down_revision: Union[str, Sequence[str], None] = "4cd55687949f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str, schema: str | None = None) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)


def upgrade() -> None:
    if not _table_exists("god_cases"):
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
