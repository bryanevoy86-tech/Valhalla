"""pack_127_integrity_events

Revision ID: f27c3d4e5f67
Revises: f26b2c3d4e56
Create Date: 2025-11-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "f27c3d4e5f67"
down_revision: Union[str, Sequence[str], None] = "f26b2c3d4e56"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    cols = []
    if "integrity_events" in inspector.get_table_names():
        existing_cols = {c["name"] for c in inspector.get_columns("integrity_events")}
        wanted = {
            "event_type": sa.String(),
            "severity": sa.String(),
            "actor_type": sa.String(),
            "actor_name": sa.String(),
            "legacy_code": sa.String(),
            "vault_name": sa.String(),
            "amount": sa.Float(),
            "currency": sa.String(),
            "description": sa.Text(),
            "metadata_json": sa.Text(),
            "requires_human_review": sa.Boolean(),
            "reviewed": sa.Boolean(),
            "review_note": sa.Text(),
        }
        for col_name, col_type in wanted.items():
            if col_name not in existing_cols:
                op.add_column("integrity_events", sa.Column(col_name, col_type))
    else:
        op.create_table(
            "integrity_events",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("event_type", sa.String(), nullable=False),
            sa.Column("severity", sa.String(), server_default="info"),
            sa.Column("actor_type", sa.String(), nullable=False),
            sa.Column("actor_name", sa.String(), nullable=False),
            sa.Column("legacy_code", sa.String()),
            sa.Column("vault_name", sa.String()),
            sa.Column("amount", sa.Float(), server_default="0.0"),
            sa.Column("currency", sa.String(), server_default="CAD"),
            sa.Column("description", sa.Text()),
            sa.Column("metadata_json", sa.Text()),
            sa.Column("requires_human_review", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("reviewed", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("review_note", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
        )
        op.create_index("ix_integrity_events_event_type", "integrity_events", ["event_type"])
        op.create_index("ix_integrity_events_severity", "integrity_events", ["severity"])
        op.create_index("ix_integrity_events_actor_name", "integrity_events", ["actor_name"])


def downgrade() -> None:
    # best effort: only drop if table was created by this migration (has event_type column mandatory)
    bind = op.get_bind()
    inspector = inspect(bind)
    if "integrity_events" in inspector.get_table_names():
        existing_cols = {c["name"] for c in inspector.get_columns("integrity_events")}
        if {"event_type", "actor_name"}.issubset(existing_cols):
            op.drop_index("ix_integrity_events_actor_name", table_name="integrity_events")
            op.drop_index("ix_integrity_events_severity", table_name="integrity_events")
            op.drop_index("ix_integrity_events_event_type", table_name="integrity_events")
            op.drop_table("integrity_events")
