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


def downgrade() -> None:
    op.drop_index("ix_freeze_events_severity", table_name="freeze_events")
    op.drop_index("ix_freeze_events_event_type", table_name="freeze_events")
    op.drop_index("ix_freeze_events_created_at", table_name="freeze_events")
    op.drop_table("freeze_events")
