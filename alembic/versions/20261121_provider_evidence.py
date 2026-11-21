"""Store scored synthetic provider comparison receipts."""
from alembic import op
import sqlalchemy as sa

revision = "20261121_provider_evidence"
down_revision = "20261121_norns_forecasts"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_provider_evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("vendor", sa.String(40), nullable=False),
        sa.Column("model", sa.String(160), nullable=False),
        sa.Column("role", sa.String(40), nullable=False),
        sa.Column("suite_version", sa.Integer(), nullable=False),
        sa.Column("input_digest", sa.String(64), nullable=False),
        sa.Column("fixture_results", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prime_provider_evidence_provider_id", "prime_provider_evidence", ["provider_id"])


def downgrade():
    # Retain comparison evidence during an application rollback.
    pass
