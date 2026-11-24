"""Store provider event identities and independently read processor evidence."""
from alembic import op
import sqlalchemy as sa

revision = "20261123_stripe_finance"
down_revision = "20261123_tuning_profile_identity"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stripe_financial_events",
        sa.Column("event_id", sa.String(128), primary_key=True),
        sa.Column("livemode", sa.Boolean(), nullable=False),
        sa.Column("payload_sha256", sa.String(64), nullable=False),
        sa.Column("snapshot_sha256", sa.String(64), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "stripe_balance_evidence",
        sa.Column("event_id", sa.String(128), sa.ForeignKey("stripe_financial_events.event_id"), primary_key=True),
        sa.Column("livemode", sa.Boolean(), nullable=False),
        sa.Column("payment_intent_id", sa.String(128), nullable=False),
        sa.Column("balance_transaction_id", sa.String(128), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("evidence_sha256", sa.String(64), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("livemode", "balance_transaction_id", name="uq_stripe_balance_transaction"),
        sa.UniqueConstraint("livemode", "payment_intent_id", name="uq_stripe_balance_capture"),
    )


def downgrade():
    # Preserve used provider identities and evidence on rollback.
    pass
