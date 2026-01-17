"""merge heads + add go_live_state table

Revision ID: 20260113_golive_merge
Revises: v3_10_integrity_events, 9e9f0b8c7f91, pack_64_contract_engine, pack_65_buyer_match
Create Date: 2026-01-13

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260113_golive_merge"
down_revision = ("v3_10_integrity_events", "9e9f0b8c7f91", "pack_64_contract_engine", "pack_65_buyer_match")
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "go_live_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("go_live_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("kill_switch_engaged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("changed_by", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.execute(
        "INSERT INTO go_live_state (id, go_live_enabled, kill_switch_engaged, updated_at) "
        "VALUES (1, false, false, CURRENT_TIMESTAMP)"
    )


def downgrade():
    op.drop_table("go_live_state")
