"""Persist scoped investment and FX source evidence."""
from alembic import op
import sqlalchemy as sa

revision = "20261122_market_evidence"
down_revision = "20261122_campaign_rehearsal"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_market_evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("scope_key", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(12), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_prime_market_evidence_scope_key", "prime_market_evidence", ["scope_key"])


def downgrade():
    # Keep time-stamped source evidence and revocation history.
    pass
