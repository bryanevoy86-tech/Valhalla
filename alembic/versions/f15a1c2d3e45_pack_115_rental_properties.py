"""pack_115_rental_properties

Revision ID: f15a1c2d3e45
Revises: e54f9c1d7f45
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "f15a1c2d3e45"
down_revision = "e54f9c1d7f45"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "rental_properties" not in inspect(bind).get_table_names():
        op.create_table(
            "rental_properties",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("legacy_code", sa.String(), nullable=False),
            sa.Column("zone_code", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("address_line1", sa.String(), nullable=False),
            sa.Column("address_line2", sa.String()),
            sa.Column("city", sa.String()),
            sa.Column("region", sa.String()),
            sa.Column("country", sa.String(), nullable=False),
            sa.Column("postal_code", sa.String()),
            sa.Column("property_type", sa.String(), server_default=sa.text("'single'")),
            sa.Column("bedrooms", sa.Integer(), server_default=sa.text("0")),
            sa.Column("bathrooms", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("square_feet", sa.Integer(), server_default=sa.text("0")),
            sa.Column("purchase_price", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("arv", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("current_value", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("status", sa.String(), server_default=sa.text("'acquisition'")),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_rental_properties_id", "rental_properties", ["id"], unique=False)
        op.create_index("ix_rental_properties_legacy_code", "rental_properties", ["legacy_code"], unique=False)
        op.create_index("ix_rental_properties_zone_code", "rental_properties", ["zone_code"], unique=False)
        op.create_index("ix_rental_properties_status", "rental_properties", ["status"], unique=False)


def downgrade():
    op.drop_index("ix_rental_properties_status", table_name="rental_properties")
    op.drop_index("ix_rental_properties_zone_code", table_name="rental_properties")
    op.drop_index("ix_rental_properties_legacy_code", table_name="rental_properties")
    op.drop_index("ix_rental_properties_id", table_name="rental_properties")
    op.drop_table("rental_properties")
