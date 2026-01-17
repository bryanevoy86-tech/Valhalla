"""pack_111_legacy_performance

Revision ID: b21e6f8a4c12
Revises: a10f5d7c3e01
Create Date: 2025-11-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "b21e6f8a4c12"
down_revision: Union[str, Sequence[str], None] = "a10f5d7c3e01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "legacy_performance" not in insp.get_table_names():
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
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_legacy_performance_id", "legacy_performance", ["id"], unique=False)
        op.create_index("ix_legacy_performance_legacy_code", "legacy_performance", ["legacy_code"], unique=False)
        op.create_index("ix_legacy_performance_period", "legacy_performance", ["period"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_legacy_performance_period", table_name="legacy_performance")
    op.drop_index("ix_legacy_performance_legacy_code", table_name="legacy_performance")
    op.drop_index("ix_legacy_performance_id", table_name="legacy_performance")
    op.drop_table("legacy_performance")
