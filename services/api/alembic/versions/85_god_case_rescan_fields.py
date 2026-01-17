"""add rescan fields to god_cases

Revision ID: 85_god_case_rescan_fields
Revises: 84_specialist_feedback
Create Date: 2025-11-21 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "85_god_case_rescan_fields"
down_revision: Union[str, None] = "84_specialist_feedback"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = insp.get_columns(table_name)
    return any(col["name"] == column_name for col in columns)


def upgrade() -> None:
    # New lifecycle fields for GodCase rescan logic
    if not _column_exists("god_cases", "rescan_count"):
        op.add_column(
            "god_cases",
            sa.Column("rescan_count", sa.Integer(), nullable=False, server_default="0"),
        )
    
    if not _column_exists("god_cases", "last_rescan_at"):
        op.add_column(
            "god_cases",
            sa.Column("last_rescan_at", sa.DateTime(timezone=True), nullable=True),
        )
    
    if not _column_exists("god_cases", "last_specialist_feedback_at"):
        op.add_column(
            "god_cases",
            sa.Column(
                "last_specialist_feedback_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )

    # Drop the default now that initial backfill is done
    if _column_exists("god_cases", "rescan_count"):
        op.alter_column(
            "god_cases",
            "rescan_count",
            server_default=None,
        )


def downgrade() -> None:
    op.drop_column("god_cases", "last_specialist_feedback_at")
    op.drop_column("god_cases", "last_rescan_at")
    op.drop_column("god_cases", "rescan_count")
