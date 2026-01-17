"""pack_130_system_health_snapshots

Revision ID: f2aa0b1c2d46
Revises: f29e5f6a7b89
Create Date: 2025-11-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "f2aa0b1c2d46"
down_revision: Union[str, Sequence[str], None] = "f29e5f6a7b89"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "system_health_snapshots" not in inspector.get_table_names():
        op.create_table(
            "system_health_snapshots",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("scope", sa.String(), nullable=False),
            sa.Column("scope_code", sa.String()),
            sa.Column("health_score", sa.Float(), server_default="1.0"),
            sa.Column("income_status", sa.String(), server_default="green"),
            sa.Column("liquidity_status", sa.String(), server_default="green"),
            sa.Column("deal_flow_status", sa.String(), server_default="green"),
            sa.Column("compliance_status", sa.String(), server_default="green"),
            sa.Column("ai_status", sa.String(), server_default="green"),
            sa.Column("summary", sa.Text()),
            sa.Column("details_json", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
        )
        op.create_index("ix_system_health_snapshots_scope", "system_health_snapshots", ["scope"])
        op.create_index("ix_system_health_snapshots_created", "system_health_snapshots", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_system_health_snapshots_created", table_name="system_health_snapshots")
    op.drop_index("ix_system_health_snapshots_scope", table_name="system_health_snapshots")
    op.drop_table("system_health_snapshots")
