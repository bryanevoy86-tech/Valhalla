"""Store scoped Foundry source records."""
from alembic import op
import sqlalchemy as sa

revision = "20261121_foundry_evidence"
down_revision = "20261121_attachment_reviews"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_foundry_evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("scope_key", sa.String(64), nullable=False),
        sa.Column("source_ref", sa.String(240), nullable=False),
        sa.Column("observed_on", sa.Date(), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("scope_key", "source_ref", "observed_on", name="uq_foundry_observation"),
    )
    op.create_index("ix_foundry_evidence_scope", "prime_foundry_evidence", ["scope_key", "observed_on"])


def downgrade():
    # Retain owner-approved source evidence during application rollback.
    pass
