"""Retain policy evidence on canonical freeze events."""

from alembic import op
import sqlalchemy as sa

revision = "20261120_freeze_event_evidence"
down_revision = "20261120_deal_brief_links"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("freeze_events", sa.Column("severity", sa.String(), nullable=True))
    op.add_column("freeze_events", sa.Column("reason", sa.String(), nullable=True))
    op.add_column("freeze_events", sa.Column("payload", sa.JSON(), nullable=True))
    op.add_column("freeze_events", sa.Column("resolved_by", sa.String(), nullable=True))


def downgrade():
    # Preserve historical evidence when rolling the application version back.
    pass
