"""pack_128_alert_channels_rules

Revision ID: f28d4e5f6a78
Revises: f27c3d4e5f67
Create Date: 2025-11-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "f28d4e5f6a78"
down_revision: Union[str, Sequence[str], None] = "f27c3d4e5f67"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()
    if "alert_channels" not in tables:
        op.create_table(
            "alert_channels",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("channel_type", sa.String(), nullable=False),
            sa.Column("target", sa.String(), nullable=False),
            sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
        )
        op.create_index("ix_alert_channels_active", "alert_channels", ["active"])
        op.create_index("ix_alert_channels_type", "alert_channels", ["channel_type"])

    if "alert_rules" not in tables:
        op.create_table(
            "alert_rules",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("event_type", sa.String(), nullable=False),
            sa.Column("min_severity", sa.String(), server_default="info"),
            sa.Column("channel_id", sa.Integer(), nullable=False),
            sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
        )
        op.create_index("ix_alert_rules_event_type", "alert_rules", ["event_type"])
        op.create_index("ix_alert_rules_active", "alert_rules", ["active"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "alert_rules" in inspector.get_table_names():
        op.drop_index("ix_alert_rules_active", table_name="alert_rules")
        op.drop_index("ix_alert_rules_event_type", table_name="alert_rules")
        op.drop_table("alert_rules")
    if "alert_channels" in inspector.get_table_names():
        op.drop_index("ix_alert_channels_type", table_name="alert_channels")
        op.drop_index("ix_alert_channels_active", table_name="alert_channels")
        op.drop_table("alert_channels")
