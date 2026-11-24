"""Durable Stripe renewal failure and backoff state."""
from alembic import op
import sqlalchemy as sa

revision = "20261123_stripe_recurring_worker"
down_revision = "20261123_stripe_recurring"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stripe_recurring_attempts",
        sa.Column("event_id", sa.String(128), sa.ForeignKey("stripe_financial_events.event_id"), primary_key=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("retry_at", sa.DateTime(timezone=True)),
    )


def downgrade():
    # Keep failure and review state across application rollbacks.
    pass
