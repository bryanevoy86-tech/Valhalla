"""Persist prospective Norns holdout membership."""
from alembic import op
import sqlalchemy as sa

revision = "20261122_norns_holdout"
down_revision = "20261122_provider_pricing"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_norns_holdout",
        sa.Column("forecast_id", sa.Uuid(), sa.ForeignKey("prime_norns_forecasts.id"), primary_key=True),
        sa.Column("enrolled_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    # Retain independent evaluation membership.
    pass
