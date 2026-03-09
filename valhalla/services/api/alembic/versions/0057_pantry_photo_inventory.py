"""
Pack 57: Pantry Photo Inventory System
"""
from alembic import op
import sqlalchemy as sa

revision = "0057_pantry_photo_inventory"
down_revision = "0056_kings_hub_adaptive_vaults"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "pantry_locations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("notes", sa.Text)
    )
    op.create_table(
        "pantry_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("tags", sa.String(256), nullable=True),
        sa.Column("unit", sa.String(16), nullable=False, server_default="ea"),
        sa.Column("reorder_at", sa.Float, nullable=False, server_default="1"),
        sa.Column("target_qty", sa.Float, nullable=False, server_default="2"),
        sa.Column("auto_reorder", sa.Boolean, nullable=False, server_default=sa.text("true"))
    )
    op.create_table(
        "pantry_stocks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("item_id", sa.Integer, sa.ForeignKey("pantry_items.id", ondelete="CASCADE")),
        sa.Column("location_id", sa.Integer, sa.ForeignKey("pantry_locations.id", ondelete="CASCADE")),
        sa.Column("qty", sa.Float, nullable=False, server_default="0")
    )
    op.create_table(
        "pantry_photos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("item_id", sa.Integer, sa.ForeignKey("pantry_items.id", ondelete="SET NULL")),
        sa.Column("file_name", sa.String(256), nullable=False),
        sa.Column("alt_text", sa.String(256), nullable=True),
        sa.Column("detected_tags", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    op.create_table(
        "pantry_txns",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("item_id", sa.Integer, sa.ForeignKey("pantry_items.id", ondelete="CASCADE")),
        sa.Column("location_id", sa.Integer, sa.ForeignKey("pantry_locations.id", ondelete="CASCADE")),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("qty", sa.Float, nullable=False),
        sa.Column("note", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    op.create_table(
        "pantry_reorders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("item_id", sa.Integer, sa.ForeignKey("pantry_items.id", ondelete="CASCADE")),
        sa.Column("suggested_qty", sa.Float, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="suggested"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )


def downgrade():
    op.drop_table("pantry_reorders")
    op.drop_table("pantry_txns")
    op.drop_table("pantry_photos")
    op.drop_table("pantry_stocks")
    op.drop_table("pantry_items")
    op.drop_table("pantry_locations")
