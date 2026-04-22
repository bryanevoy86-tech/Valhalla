"""add_audit_log

Revision ID: 20260422_003
Revises: 20260422_002
Create Date: 2026-04-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260422_003"
down_revision: Union[str, Sequence[str], None] = "20260422_002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create audit_log table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Only create table if it doesn't exist
    if "audit_log" not in inspector.get_table_names():
        op.create_table(
            "audit_log",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("deal_id", sa.Integer, nullable=True),
            sa.Column("event_type", sa.String(60), nullable=False),
            sa.Column("event_source", sa.String(20), nullable=False, server_default="system"),
            sa.Column("message", sa.String(500), nullable=False),
            sa.Column("metadata", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_audit_log_deal_id", "audit_log", ["deal_id"])
        op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])
        op.create_index("ix_audit_log_event_type", "audit_log", ["event_type"])


def downgrade() -> None:
    """Drop audit_log table."""
    op.drop_index("ix_audit_log_event_type", table_name="audit_log")
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_deal_id", table_name="audit_log")
    op.drop_table("audit_log")
