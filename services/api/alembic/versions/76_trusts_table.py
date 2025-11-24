"""add trusts table

Revision ID: 76_trusts_table
Revises: 75_resort_bookings_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa

revision = "76_trusts_table"
down_revision = "75_resort_bookings_table"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "trusts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("jurisdiction", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="active"),
        sa.Column("routing_priority", sa.Integer(), server_default="1"),
        sa.Column("tax_exempt", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("vault_balance", sa.Float(), server_default="0.0"),
        sa.Column("created_at", sa.DateTime())
    )

def downgrade():
    op.drop_table("trusts")
