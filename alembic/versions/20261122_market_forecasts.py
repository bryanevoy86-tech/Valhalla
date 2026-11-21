"""Persist independently sourced prospective market forecasts under Norns."""
from alembic import op
import sqlalchemy as sa

revision = "20261122_market_forecasts"
down_revision = "20261122_market_evidence"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_norns_market_forecasts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("scope_key", sa.String(64), nullable=False),
        sa.Column("target_key", sa.String(64), nullable=False, unique=True),
        sa.Column("evidence_class", sa.String(20), nullable=False),
        sa.Column("probability_bp", sa.Integer(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("observed_outcome", sa.Integer()),
        sa.Column("settlement", sa.JSON()),
        sa.CheckConstraint("probability_bp BETWEEN 0 AND 10000", name="ck_market_forecast_probability"),
        sa.CheckConstraint("observed_outcome IS NULL OR observed_outcome IN (0, 1)", name="ck_market_forecast_outcome"),
    )
    op.create_index("ix_prime_norns_market_forecasts_scope_key", "prime_norns_market_forecasts", ["scope_key"])


def downgrade():
    # Preserve prospective samples and resolution records.
    pass
