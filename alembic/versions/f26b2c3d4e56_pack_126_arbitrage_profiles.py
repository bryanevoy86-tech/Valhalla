"""pack_126_arbitrage_profiles

Revision ID: f26b2c3d4e56
Revises: f25a1b2c3d45
Create Date: 2025-11-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "f26b2c3d4e56"
down_revision: Union[str, Sequence[str], None] = "f25a1b2c3d45"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "arbitrage_profiles" not in inspector.get_table_names():
        op.create_table(
            "arbitrage_profiles",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False, unique=True),
            sa.Column("pool_type", sa.String(), nullable=False),
            sa.Column("risk_level", sa.Float(), server_default="0.3"),
            sa.Column("liquidity_priority", sa.Float(), server_default="0.9"),
            sa.Column("max_exposure_fraction", sa.Float(), server_default="0.5"),
            sa.Column("min_cash_buffer_fraction", sa.Float(), server_default="0.2"),
            sa.Column("auto_trading_enabled", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )
        op.create_index("ix_arbitrage_profiles_name", "arbitrage_profiles", ["name"], unique=True)
        op.create_index("ix_arbitrage_profiles_pool_type", "arbitrage_profiles", ["pool_type"])


def downgrade() -> None:
    op.drop_index("ix_arbitrage_profiles_pool_type", table_name="arbitrage_profiles")
    op.drop_index("ix_arbitrage_profiles_name", table_name="arbitrage_profiles")
    op.drop_table("arbitrage_profiles")
