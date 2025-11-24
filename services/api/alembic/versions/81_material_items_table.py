"""add material items table

Revision ID: 81_material_items_table
Revises: 80_underwriter_assessments_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa

revision = "81_material_items_table"
down_revision = "80_underwriter_assessments_table"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "material_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String()),
        sa.Column("unit", sa.String(), server_default="unit"),
        sa.Column("preferred_supplier", sa.String()),
        sa.Column("last_price", sa.Float(), server_default="0.0"),
        sa.Column("currency", sa.String(), server_default="CAD"),
        sa.Column("region", sa.String()),
        sa.Column("notes", sa.String()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

def downgrade():
    op.drop_table("material_items")
