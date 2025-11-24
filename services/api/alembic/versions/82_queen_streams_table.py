"""add queen streams table

Revision ID: 82_queen_streams_table
Revises: 81_material_items_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa

revision = "82_queen_streams_table"
down_revision = "81_material_items_table"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "queen_streams",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String()),
        sa.Column("status", sa.String(), server_default="active"),
        sa.Column("monthly_target", sa.Float(), server_default="0.0"),
        sa.Column("current_estimate", sa.Float(), server_default="0.0"),
        sa.Column("auto_tax_handled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("auto_vault_allocation", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("notes", sa.String()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

def downgrade():
    op.drop_table("queen_streams")
