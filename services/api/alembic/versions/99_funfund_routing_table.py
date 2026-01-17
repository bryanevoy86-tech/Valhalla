"""Pack 101: add funfund_routing table

Revision ID: 99_funfund_routing_table
Revises: 98_ai_personas_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "99_funfund_routing_table"
down_revision = "98_ai_personas_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "funfund_routing" not in inspect(bind).get_table_names():
        op.create_table(
            "funfund_routing",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("profile_name", sa.String(), nullable=False, unique=True),
            sa.Column("arbitrage_percent", sa.Float(), server_default=sa.text("1.0")),
            sa.Column("min_liquid_balance", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("max_liquid_balance", sa.Float(), server_default=sa.text("1000000.0")),
            sa.Column("risk_profile", sa.String(), server_default=sa.text("'moderate'")),
            sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("description", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("funfund_routing")
