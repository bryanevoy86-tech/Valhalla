"""Bind signed payment fixtures to reconciled local statement entries."""
from alembic import op
import sqlalchemy as sa

revision = "20261123_fixture_settlement"
down_revision = "20261123_owner_retention"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_foundry_fixture_settlements",
        sa.Column("payment_event_id", sa.String(120),
                  sa.ForeignKey("prime_foundry_rehearsal_payments.event_id"), primary_key=True),
        sa.Column("statement_entry_key", sa.String(64), nullable=False, unique=True),
        sa.Column("statement_id", sa.Uuid(), nullable=False),
        sa.Column("statement_sha256", sa.String(64), nullable=False),
        sa.Column("payment_sha256", sa.String(64), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
    )


def downgrade():
    # Retain prior reconciliation evidence and consumed statement identities.
    pass
