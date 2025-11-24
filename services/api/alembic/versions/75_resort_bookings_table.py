"""add resort bookings table

Revision ID: 75_resort_bookings_table
Revises: 74_contractors_table
Create Date: 2025-11-24

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '75_resort_bookings_table'
down_revision = '74_contractors_table'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "resort_bookings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("guest_name", sa.String(), nullable=False),
        sa.Column("check_in", sa.DateTime()),
        sa.Column("check_out", sa.DateTime()),
        sa.Column("room_type", sa.String()),
        sa.Column("base_price", sa.Float()),
        sa.Column("dynamic_price", sa.Float()),
        sa.Column("status", sa.String(), server_default="reserved"),
        sa.Column("created_at", sa.DateTime())
    )


def downgrade():
    op.drop_table("resort_bookings")
