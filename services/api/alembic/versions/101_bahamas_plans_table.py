"""Pack 103: add bahamas_plans table

Revision ID: 101_bahamas_plans_table
Revises: 100_truck_plans_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "101_bahamas_plans_table"
down_revision = "100_truck_plans_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "bahamas_plans" not in inspect(bind).get_table_names():
        op.create_table(
            "bahamas_plans",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("residency_target", sa.Float(), nullable=False),
            sa.Column("residency_vault_balance", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("resort_target_price_min", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("resort_target_price_max", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("resort_vault_balance", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("trigger_residency_ready", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("trigger_resort_search_active", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("bahamas_plans")
