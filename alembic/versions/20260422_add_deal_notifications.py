"""add_deal_notifications

Revision ID: 20260422_002
Revises: 20260422_001, 5e5bb3b591a4
Create Date: 2026-04-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260422_002"
down_revision: Union[str, Sequence[str], None] = ("20260422_001", "5e5bb3b591a4")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create deal_notifications table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Only create table if it doesn't exist
    if "deal_notifications" not in inspector.get_table_names():
        op.create_table(
            "deal_notifications",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("deal_id", sa.Integer, sa.ForeignKey("deal_briefs.id"), nullable=True),
            sa.Column("type", sa.String(60), nullable=False),
            sa.Column("title", sa.String(240), nullable=False),
            sa.Column("message", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.text("false")),
        )
        op.create_index("ix_deal_notifications_deal_id", "deal_notifications", ["deal_id"])
        op.create_index("ix_deal_notifications_created_at", "deal_notifications", ["created_at"])


def downgrade() -> None:
    """Drop deal_notifications table."""
    op.drop_index("ix_deal_notifications_created_at", table_name="deal_notifications")
    op.drop_index("ix_deal_notifications_deal_id", table_name="deal_notifications")
    op.drop_table("deal_notifications")
