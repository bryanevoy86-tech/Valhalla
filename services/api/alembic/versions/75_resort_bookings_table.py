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


def _table_exists(name: str, schema: str | None = None) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)


def upgrade():
    if not _table_exists("resort_bookings"):
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
