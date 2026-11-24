"""Persist internal buyer claim expiration."""

from alembic import op
import sqlalchemy as sa

revision = "20261120_buyer_claim_expiry"
down_revision = "20261120_closer_sessions"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("deal_buyer_matches", sa.Column("claim_expires_at", sa.DateTime(), nullable=True))


def downgrade():
    # Keep the recorded claim expirations if rolling back the application.
    pass
