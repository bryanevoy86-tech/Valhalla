"""Pack 110: extend empire_snapshots with metrics columns

Revision ID: 103_empire_snapshots_extend
Revises: 102_trust_status_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "103_empire_snapshots_extend"
down_revision = "102_trust_status_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = inspect(bind)
    if "empire_snapshots" in insp.get_table_names():
        cols = {c.get("name"): c for c in insp.get_columns("empire_snapshots")}
        def add(name, type_, **kwargs):
            if name not in cols:
                op.add_column("empire_snapshots", sa.Column(name, type_, **kwargs))
        add("period", sa.String(), nullable=True)
        add("period_label", sa.String(), nullable=True)
        add("gross_income", sa.Float(), nullable=True, server_default=sa.text("0.0"))
        add("taxes_reserved", sa.Float(), nullable=True, server_default=sa.text("0.0"))
        add("reinvestment", sa.Float(), nullable=True, server_default=sa.text("0.0"))
        add("fun_fund", sa.Float(), nullable=True, server_default=sa.text("0.0"))
        add("legacy_count", sa.Integer(), nullable=True, server_default=sa.text("0"))
        add("active_zones", sa.Integer(), nullable=True, server_default=sa.text("0"))
        add("brRRR_count", sa.Integer(), nullable=True, server_default=sa.text("0"))
        add("flip_count", sa.Integer(), nullable=True, server_default=sa.text("0"))
        add("wholesale_count", sa.Integer(), nullable=True, server_default=sa.text("0"))
        add("resort_count", sa.Integer(), nullable=True, server_default=sa.text("0"))
        add("shield_mode_active", sa.Boolean(), nullable=True, server_default=sa.text("false"))
        add("black_ice_armed", sa.Boolean(), nullable=True, server_default=sa.text("false"))
        add("bahamas_ready", sa.Boolean(), nullable=True, server_default=sa.text("false"))


def downgrade():
    # Non-destructive downgrade: leave columns in place (avoid data loss)
    pass
