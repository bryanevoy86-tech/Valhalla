"""Add durable private closer sessions."""

from alembic import op
import sqlalchemy as sa

revision = "20261120_closer_sessions"
down_revision = "20261120_freeze_event_evidence"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "closer_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("deal_id", sa.Integer(), sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("script", sa.JSON(), nullable=False),
        sa.Column("last_section", sa.String(32), nullable=False),
        sa.Column("section_notes", sa.JSON(), nullable=False),
        sa.Column("feedback", sa.JSON()),
    )
    op.create_index("ix_closer_sessions_deal_id", "closer_sessions", ["deal_id"])


def downgrade():
    # Retain private notes if the application version is rolled back.
    pass
