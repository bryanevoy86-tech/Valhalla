"""Persist licensed local Foundry adapter work."""
from alembic import op
import sqlalchemy as sa

revision = "20261123_startup_intake"
down_revision = "20261122_economic_control"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_foundry_intake_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("observation_key", sa.String(64), unique=True, nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=False),
        sa.Column("error_code", sa.String(40)),
    )
    op.create_index("ix_foundry_intake_pending", "prime_foundry_intake_jobs", ["status", "next_attempt_at"])


def downgrade():
    # Preserve licensed research and queue history.
    pass
