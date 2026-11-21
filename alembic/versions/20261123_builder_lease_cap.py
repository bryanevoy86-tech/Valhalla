"""Cap interrupted Builder claims using a persisted lease counter."""
from alembic import op
import sqlalchemy as sa

revision = "20261123_builder_lease_cap"
down_revision = "20261123_fixture_settlement"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("prime_builder_assignments", sa.Column("claim_count", sa.Integer(), nullable=False, server_default="0"))
    op.execute("UPDATE prime_builder_assignments SET claim_count = 1 WHERE lease_id IS NOT NULL")


def downgrade():
    # Do not reset interruption history during a rollback.
    pass
