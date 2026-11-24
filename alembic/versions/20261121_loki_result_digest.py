"""Bind independently published findings to their immutable receipt."""
from alembic import op
import sqlalchemy as sa

revision = "20261121_loki_result_digest"
down_revision = "20261121_specialist_assignments"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("loki_independent_receipts", sa.Column("result_sha256", sa.String(64)))


def downgrade():
    # Preserve result integrity metadata during application rollback.
    pass
