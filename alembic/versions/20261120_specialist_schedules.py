"""Create durable Prime specialist schedules."""
from alembic import op
import sqlalchemy as sa


revision = "20261120_specialist_schedules"
down_revision = "20261120_loki_review_receipts"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_specialist_schedules",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("request", sa.JSON(), nullable=False),
        sa.Column("cadence_seconds", sa.Integer(), nullable=False),
        sa.Column("next_due_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("last_report_event_id", sa.String(80)),
        sa.CheckConstraint("cadence_seconds BETWEEN 300 AND 86400", name="ck_prime_specialist_cadence"),
    )
    op.create_index("ix_prime_specialist_due", "prime_specialist_schedules", ["state", "next_due_at"])


def downgrade():
    # Keep owner mandates and their evidence available after an application rollback.
    pass
