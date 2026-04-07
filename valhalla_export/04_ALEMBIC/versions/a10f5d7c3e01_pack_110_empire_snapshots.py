"""pack_110_empire_snapshots

Revision ID: a10f5d7c3e01
Revises: fdc9b660a48f
Create Date: 2025-11-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "a10f5d7c3e01"
down_revision: Union[str, Sequence[str], None] = "102_trust_status_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "empire_snapshots" not in insp.get_table_names():
        op.create_table(
            "empire_snapshots",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("label", sa.String(), nullable=True),
            sa.Column("snapshot_type", sa.String(), server_default=sa.text("'manual'")),
            sa.Column("summary_json", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text()),
            sa.Column("period", sa.String(), nullable=True, server_default=sa.text("'month'")),
            sa.Column("period_label", sa.String(), nullable=True),
            sa.Column("gross_income", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("taxes_reserved", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("reinvestment", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("fun_fund", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("legacy_count", sa.Integer(), server_default=sa.text("0")),
            sa.Column("active_zones", sa.Integer(), server_default=sa.text("0")),
            sa.Column("brRRR_count", sa.Integer(), server_default=sa.text("0")),
            sa.Column("flip_count", sa.Integer(), server_default=sa.text("0")),
            sa.Column("wholesale_count", sa.Integer(), server_default=sa.text("0")),
            sa.Column("resort_count", sa.Integer(), server_default=sa.text("0")),
            sa.Column("shield_mode_active", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("black_ice_armed", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("bahamas_ready", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_empire_snapshots_id", "empire_snapshots", ["id"], unique=False)
        op.create_index("ix_empire_snapshots_period", "empire_snapshots", ["period"], unique=False)
        op.create_index("ix_empire_snapshots_snapshot_type", "empire_snapshots", ["snapshot_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_empire_snapshots_snapshot_type", table_name="empire_snapshots")
    op.drop_index("ix_empire_snapshots_period", table_name="empire_snapshots")
    op.drop_index("ix_empire_snapshots_id", table_name="empire_snapshots")
    op.drop_table("empire_snapshots")
