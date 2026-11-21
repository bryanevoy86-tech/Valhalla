"""Distinguish prospective worker estimates and retain training lineage."""
from alembic import op
import sqlalchemy as sa

revision = "20261121_norns_scoped_history"
down_revision = "20261121_builder_assignments"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("prime_norns_forecasts", sa.Column(
        "estimate_source", sa.String(40), nullable=False, server_default="OWNER_ESTIMATE",
    ))
    op.add_column("prime_norns_forecasts", sa.Column("training_evidence", sa.JSON()))


def downgrade():
    # Preserve the lineage of measured forecasts.
    pass
