"""Bind the owner's disposition to the exact independent findings receipt."""
from alembic import op
import sqlalchemy as sa

revision = "20261123_loki_disposition_binding"
down_revision = "20261123_stripe_recurring_worker"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("loki_reconsiderations", sa.Column("decision_sha256", sa.String(64), nullable=True))


def downgrade():
    # Keep the decision provenance through an application rollback.
    pass
