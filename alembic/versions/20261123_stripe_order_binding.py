"""Bind external Stripe intent identifiers to specific Valhalla product orders."""
from alembic import op
import sqlalchemy as sa

revision = "20261123_stripe_order_binding"
down_revision = "20261123_stripe_finance"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stripe_order_bindings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("livemode", sa.Boolean(), nullable=False),
        sa.Column("payment_intent_id", sa.String(128), nullable=False),
        sa.Column("binding", sa.JSON(), nullable=False),
        sa.Column("binding_sha256", sa.String(64), nullable=False),
        sa.UniqueConstraint("livemode", "payment_intent_id", name="uq_stripe_order_intent"),
    )


def downgrade():
    # Retain intent identities to prevent binding the same payment again.
    pass
