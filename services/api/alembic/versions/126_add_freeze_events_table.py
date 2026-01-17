"""Add freeze_events table.

This fixes scheduler crashes where Postgres reports:
  relation "freeze_events" does not exist
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# IMPORTANT:
# - Set `down_revision` to your latest revision ID from `alembic history`.
# - `revision` can be any unique string (keep as-is unless it conflicts).

revision = "126_freeze_events_table"
down_revision = "e75b30975c5f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if table already exists (old schema compatibility)
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if "freeze_events" not in inspector.get_table_names():
        # Table doesn't exist - create it with new schema
        op.create_table(
            "freeze_events",
            sa.Column("id", sa.Integer, primary_key=True, nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "source",
                sa.String(length=100),
                nullable=True,
                comment="What triggered the freeze (scheduler job, policy, manual, etc.)",
            ),
            sa.Column(
                "event_type",
                sa.String(length=50),
                nullable=True,
                comment="Short code for the freeze reason (e.g. 'liquidity', 'policy_violation').",
            ),
            sa.Column(
                "reason",
                sa.Text,
                nullable=True,
                comment="Human-readable reason for the freeze.",
            ),
            sa.Column(
                "severity",
                sa.String(length=20),
                nullable=True,
                comment="Optional severity level (info/warn/critical).",
            ),
            sa.Column(
                "payload",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
                comment="Optional structured data captured at freeze time.",
            ),
            sa.Column(
                "resolved_at",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="When (if) this freeze event was fully resolved.",
            ),
            sa.Column(
                "resolved_by",
                sa.String(length=100),
                nullable=True,
                comment="Who or what resolved the freeze (user, job, Heimdall).",
            ),
            sa.Column(
                "notes",
                sa.Text,
                nullable=True,
                comment="Free-form notes for extra context.",
            ),
        )

        op.create_index(
            "ix_freeze_events_created_at",
            "freeze_events",
            ["created_at"],
        )
        op.create_index(
            "ix_freeze_events_event_type",
            "freeze_events",
            ["event_type"],
        )
        op.create_index(
            "ix_freeze_events_severity",
            "freeze_events",
            ["severity"],
        )
    else:
        # Table exists with old schema - migrate it
        existing_columns = {col["name"] for col in inspector.get_columns("freeze_events")}
        
        # Add new columns if they don't exist
        if "source" not in existing_columns:
            op.add_column("freeze_events", sa.Column("source", sa.String(length=100), nullable=True))
        
        if "event_type" not in existing_columns:
            op.add_column("freeze_events", sa.Column("event_type", sa.String(length=50), nullable=True))
        
        if "reason" not in existing_columns:
            op.add_column("freeze_events", sa.Column("reason", sa.Text, nullable=True))
        
        if "severity" not in existing_columns:
            op.add_column("freeze_events", sa.Column("severity", sa.String(length=20), nullable=True))
        
        if "payload" not in existing_columns:
            op.add_column("freeze_events", sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        
        if "resolved_at" not in existing_columns:
            op.add_column("freeze_events", sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))
        
        if "resolved_by" not in existing_columns:
            op.add_column("freeze_events", sa.Column("resolved_by", sa.String(length=100), nullable=True))
        
        if "notes" not in existing_columns:
            op.add_column("freeze_events", sa.Column("notes", sa.Text, nullable=True))
        
        # Create indexes if they don't exist
        existing_indexes = {idx["name"] for idx in inspector.get_indexes("freeze_events")}
        
        if "ix_freeze_events_created_at" not in existing_indexes:
            op.create_index("ix_freeze_events_created_at", "freeze_events", ["created_at"])
        
        if "ix_freeze_events_event_type" not in existing_indexes:
            op.create_index("ix_freeze_events_event_type", "freeze_events", ["event_type"])
        
        if "ix_freeze_events_severity" not in existing_indexes:
            op.create_index("ix_freeze_events_severity", "freeze_events", ["severity"])


def downgrade() -> None:
    op.drop_index("ix_freeze_events_severity", table_name="freeze_events")
    op.drop_index("ix_freeze_events_event_type", table_name="freeze_events")
    op.drop_index("ix_freeze_events_created_at", table_name="freeze_events")
    op.drop_table("freeze_events")
