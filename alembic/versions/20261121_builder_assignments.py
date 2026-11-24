"""Persist Builder test assignments and expiring worker leases."""
from alembic import op
import sqlalchemy as sa

revision = "20261121_builder_assignments"
down_revision = "20261121_specialist_probes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_builder_assignments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("base_commit", sa.String(40), nullable=False),
        sa.Column("bundle_sha256", sa.String(64), nullable=False),
        sa.Column("image_id", sa.String(71), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("lease_id", sa.Uuid()),
        sa.Column("lease_until", sa.DateTime()),
        sa.Column("receipt", sa.JSON()),
    )
    op.create_index("ix_prime_builder_assignments_status", "prime_builder_assignments", ["status"])


def downgrade():
    # Preserve assignments and their archived test evidence.
    pass
