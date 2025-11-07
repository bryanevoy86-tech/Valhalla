"""
Pack 53: Black Ice Tier II + Shadow Contingency
"""
from alembic import op
import sqlalchemy as sa

revision = "0053_black_ice_tier2"
down_revision = "0052_neg_psych_enhancer"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "black_ice_protocols",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("level", sa.Integer, nullable=False, server_default="2"),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    op.create_table(
        "contingency_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("protocol_id", sa.Integer, sa.ForeignKey("black_ice_protocols.id", ondelete="CASCADE")),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("occurred_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    op.create_table(
        "key_rotation_checks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("protocol_id", sa.Integer, sa.ForeignKey("black_ice_protocols.id", ondelete="CASCADE")),
        sa.Column("checklist_item", sa.String(64), nullable=False),
        sa.Column("checked", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("checked_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    op.create_table(
        "continuity_windows",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("protocol_id", sa.Integer, sa.ForeignKey("black_ice_protocols.id", ondelete="CASCADE")),
        sa.Column("min_hours", sa.Integer, nullable=False, server_default="72"),
        sa.Column("alert_channel", sa.String(32), nullable=False, server_default="ops"),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text, nullable=True)
    )

def downgrade():
    op.drop_table("continuity_windows")
    op.drop_table("key_rotation_checks")
    op.drop_table("contingency_events")
    op.drop_table("black_ice_protocols")
