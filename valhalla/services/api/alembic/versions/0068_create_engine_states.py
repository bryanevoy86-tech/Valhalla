"""create engine_states table

Revision ID: 0068
Revises: 20260122_add_go_live_tables
Create Date: 2026-02-01
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0068"
down_revision = "20260122_add_go_live_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "engine_states",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("engine_name", sa.String(length=100), nullable=False, index=True),
        sa.Column("state", sa.String(length=50), nullable=False, server_default="unknown"),
        sa.Column("changed_by", sa.String(length=100), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    # If you want "one row per engine" enforced, add a unique constraint:
    op.create_unique_constraint("uq_engine_states_engine_name", "engine_states", ["engine_name"])


def downgrade() -> None:
    op.drop_constraint("uq_engine_states_engine_name", "engine_states", type_="unique")
    op.drop_table("engine_states")
