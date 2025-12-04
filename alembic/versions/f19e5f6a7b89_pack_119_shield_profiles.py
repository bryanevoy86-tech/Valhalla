"""pack_119_shield_profiles

Revision ID: f19e5f6a7b89
Revises: f18d4e5f6a78
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "f19e5f6a7b89"
down_revision = "f18d4e5f6a78"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "shield_profiles" not in inspect(bind).get_table_names():
        op.create_table(
            "shield_profiles",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False, unique=True),
            sa.Column("min_reserve_months", sa.Float(), server_default=sa.text("2.0")),
            sa.Column("max_active_expansions", sa.Integer(), server_default=sa.text("3")),
            sa.Column("income_drop_percent", sa.Float(), server_default=sa.text("0.30")),
            sa.Column("pause_new_clones", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("pause_new_zones", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("reduce_marketing_spend", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("stop_fun_fund_increase", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_shield_profiles_id", "shield_profiles", ["id"], unique=False)
        op.create_index("ix_shield_profiles_name", "shield_profiles", ["name"], unique=True)


def downgrade():
    op.drop_index("ix_shield_profiles_name", table_name="shield_profiles")
    op.drop_index("ix_shield_profiles_id", table_name="shield_profiles")
    op.drop_table("shield_profiles")
