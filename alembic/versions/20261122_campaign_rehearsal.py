"""Store synthetic campaign visits and bind each to a simulated order."""
from alembic import op
import sqlalchemy as sa

revision = "20261122_campaign_rehearsal"
down_revision = "20261122_norns_holdout"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_foundry_campaign_visits",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("scope_key", sa.String(64), nullable=False),
        sa.Column("order_id", sa.Uuid(), sa.ForeignKey("prime_foundry_rehearsal_orders.id"), unique=True),
    )
    op.create_index("ix_prime_foundry_campaign_visits_campaign_id", "prime_foundry_campaign_visits", ["campaign_id"])


def downgrade():
    # Retain rehearsal attribution records.
    pass
