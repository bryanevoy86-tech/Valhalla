"""Add owner retention deadlines and decision context to existing records."""
from alembic import op
import sqlalchemy as sa

revision = "20261123_owner_retention"
down_revision = "20261123_statement_fixtures"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("prime_owner_attachment_reviews", sa.Column("retain_until", sa.Date(), nullable=True))
    op.add_column("prime_owner_memory_entries", sa.Column("decision_context", sa.JSON(), nullable=True))


def downgrade():
    # Downgrading must not silently remove the validity deadline of owner dispositions.
    pass
