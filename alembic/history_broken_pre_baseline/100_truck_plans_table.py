"""Pack 102: add truck_plans table

Revision ID: 100_truck_plans_table
Revises: 99_funfund_routing_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "100_truck_plans_table"
down_revision = "99_funfund_routing_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "truck_plans" not in inspect(bind).get_table_names():
        op.create_table(
            "truck_plans",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("target_price", sa.Float(), nullable=False),
            sa.Column("wrap_budget", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("extras_budget", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("business_credit_target", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("current_business_credit", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("funfund_contribution_target", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("funfund_contributed", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("status", sa.String(), server_default=sa.text("'planning'")),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("truck_plans")
