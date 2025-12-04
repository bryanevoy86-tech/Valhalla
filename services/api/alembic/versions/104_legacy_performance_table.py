"""Pack 111: add legacy_performance table

Revision ID: 104_legacy_performance_table
Revises: 103_empire_snapshots_extend
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "104_legacy_performance_table"
down_revision = "103_empire_snapshots_extend"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "legacy_performance" not in inspect(bind).get_table_names():
        op.create_table(
            "legacy_performance",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("legacy_code", sa.String(), nullable=False),
            sa.Column("display_name", sa.String(), nullable=False),
            sa.Column("period", sa.String(), server_default=sa.text("'month'")),
            sa.Column("period_label", sa.String(), nullable=False),
            sa.Column("gross_income", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("net_profit", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("reinvestment", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("fun_fund", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("deals_closed", sa.Integer(), server_default=sa.text("0")),
            sa.Column("brRRR_units", sa.Integer(), server_default=sa.text("0")),
            sa.Column("flips", sa.Integer(), server_default=sa.text("0")),
            sa.Column("wholesale_deals", sa.Integer(), server_default=sa.text("0")),
            sa.Column("risk_flag", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("risk_note", sa.Text()),
            sa.Column("status", sa.String(), server_default=sa.text("'normal'")),
            sa.Column("created_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("legacy_performance")
