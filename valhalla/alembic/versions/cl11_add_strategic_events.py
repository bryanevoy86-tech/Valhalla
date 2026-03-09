"""Add strategic_events table for PACK CL11"""

from alembic import op
import sqlalchemy as sa

revision = "cl11_add_strategic_events"
down_revision = "cl9_add_decision_outcomes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "strategic_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("ref_id", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_strategic_events_event_type", "strategic_events", ["event_type"])
    op.create_index("ix_strategic_events_domain", "strategic_events", ["domain"])


def downgrade():
    op.drop_index("ix_strategic_events_event_type", table_name="strategic_events")
    op.drop_index("ix_strategic_events_domain", table_name="strategic_events")
    op.drop_table("strategic_events")
