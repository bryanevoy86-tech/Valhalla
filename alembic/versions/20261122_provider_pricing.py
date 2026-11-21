"""Persist dated provider prices and owner-supplied usage reconciliation."""
from alembic import op
import sqlalchemy as sa

revision = "20261122_provider_pricing"
down_revision = "20261122_foundry_checkout"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_provider_price_quotes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("vendor", sa.String(40), nullable=False),
        sa.Column("model", sa.String(160), nullable=False),
        sa.Column("source_url", sa.String(300), nullable=False),
        sa.Column("observed_on", sa.Date(), nullable=False),
        sa.Column("effective_on", sa.Date(), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("input_minor_per_million", sa.Integer(), nullable=False),
        sa.Column("output_minor_per_million", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.UniqueConstraint("provider_id", "vendor", "model", "currency", "effective_on",
                            name="uq_provider_price_identity_date"),
    )
    op.create_table(
        "prime_provider_usage_reconciliations",
        sa.Column("probe_id", sa.Uuid(), primary_key=True),
        sa.Column("quote_id", sa.Uuid(), nullable=False),
        sa.Column("statement_ref", sa.String(240), nullable=False),
        sa.Column("estimated_microminor", sa.BigInteger(), nullable=False),
        sa.Column("reported_microminor", sa.BigInteger(), nullable=False),
        sa.Column("usage_sha256", sa.String(64), nullable=False),
    )


def downgrade():
    # Retain scoped pricing and reconciliation evidence.
    pass
