"""Isolate signed fixture accounting from real settlement."""
from alembic import op
import sqlalchemy as sa

revision = "20261122_foundry_checkout"
down_revision = "20261122_saas_trial_entitlements"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_foundry_rehearsal_orders",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("action_id", sa.String(80), nullable=False),
        sa.Column("listing_sha256", sa.String(64), nullable=False),
        sa.Column("artifact_id", sa.Uuid(), nullable=False),
        sa.Column("artifact_sha256", sa.String(64), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("payment_reference", sa.String(120), unique=True, nullable=False),
        sa.Column("captured_minor", sa.Integer(), nullable=False),
        sa.Column("refunded_minor", sa.Integer(), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("0 <= refunded_minor AND refunded_minor <= captured_minor AND captured_minor <= amount_minor",
                           name="ck_foundry_rehearsal_amounts"),
    )
    op.create_table(
        "prime_foundry_rehearsal_payments",
        sa.Column("event_id", sa.String(120), primary_key=True),
        sa.Column("order_id", sa.Uuid(), sa.ForeignKey("prime_foundry_rehearsal_orders.id"), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("captured_delta", sa.Integer(), nullable=False),
        sa.Column("refunded_delta", sa.Integer(), nullable=False),
    )
    op.create_index("ix_prime_foundry_rehearsal_payments_order_id", "prime_foundry_rehearsal_payments", ["order_id"])


def downgrade():
    # Retain financial rehearsal evidence.
    pass
