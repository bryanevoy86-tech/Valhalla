"""Install the private economic mandate and rehearsal journal."""
from alembic import op
import sqlalchemy as sa

revision = "20261122_economic_control"
down_revision = "20261122_market_forecasts"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_economic_pools",
        sa.Column("currency", sa.String(3), primary_key=True),
        sa.Column("committed_minor", sa.BigInteger(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("liquidity_id", sa.Uuid()),
        sa.Column("liquidity_conflict", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.CheckConstraint("committed_minor >= 0", name="ck_economic_pool_commit"),
    )
    op.bulk_insert(sa.table("prime_economic_pools", sa.column("currency", sa.String(3)),
                            sa.column("committed_minor", sa.BigInteger()), sa.column("sequence", sa.Integer())), [
        {"currency": currency, "committed_minor": 0, "sequence": 0} for currency in ("CAD", "USD", "EUR", "GBP")
    ])
    op.create_table(
        "prime_economic_operations",
        sa.Column("scope_key", sa.String(64), primary_key=True),
        sa.Column("scope", sa.JSON(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
    )
    op.create_table(
        "prime_economic_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("scope_key", sa.String(64), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(18), nullable=False),
        sa.Column("receipt_key", sa.String(64), unique=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.UniqueConstraint("scope_key", "sequence", name="uq_economic_record_sequence"),
    )
    op.create_index("ix_prime_economic_records_scope_key", "prime_economic_records", ["scope_key"])


def downgrade():
    # Retain cumulative limits, accounting fixtures and their decision history.
    pass
