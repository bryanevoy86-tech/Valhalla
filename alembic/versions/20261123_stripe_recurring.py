"""Bind existing SaaS subscriptions to Stripe Checkout and unique paid periods."""
from alembic import op
import sqlalchemy as sa

revision = "20261123_stripe_recurring"
down_revision = "20261123_stripe_order_binding"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stripe_saas_bindings",
        sa.Column("id", sa.Integer(), sa.ForeignKey("subscriptions.id"), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("livemode", sa.Boolean(), nullable=False),
        sa.Column("binding", sa.JSON(), nullable=False),
        sa.Column("binding_sha256", sa.String(64), nullable=False),
        sa.Column("checkout_started_at", sa.DateTime(timezone=True)),
        sa.Column("checkout_session_id", sa.String(128), unique=True),
        sa.Column("provider_subscription_id", sa.String(128)),
        sa.Column("cancel_scheduled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("livemode", "tenant_id", "plan_id", name="uq_stripe_saas_tenant_plan"),
        sa.UniqueConstraint("livemode", "provider_subscription_id", name="uq_stripe_saas_native_subscription"),
    )
    op.create_index("ix_stripe_saas_bindings_tenant_id", "stripe_saas_bindings", ["tenant_id"])
    op.create_table(
        "stripe_paid_periods",
        sa.Column("invoice_id", sa.String(128), primary_key=True),
        sa.Column("binding_id", sa.Integer(), sa.ForeignKey("stripe_saas_bindings.id"), nullable=False),
        sa.Column("payment_intent_id", sa.String(128), nullable=False, unique=True),
        sa.Column("period_start", sa.Integer(), nullable=False),
        sa.Column("period_end", sa.Integer(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("evidence_sha256", sa.String(64), nullable=False),
        sa.UniqueConstraint("binding_id", "period_start", name="uq_stripe_paid_period_start"),
    )
    op.create_index("ix_stripe_paid_periods_binding_id", "stripe_paid_periods", ["binding_id"])


def downgrade():
    # Preserve consumed provider and financial identities.
    pass
