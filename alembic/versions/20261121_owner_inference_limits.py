"""Persist one-shot owner inference reservations and daily usage."""
from alembic import op
import sqlalchemy as sa

revision = "20261121_owner_inference_limits"
down_revision = "20261120_specialist_triggers"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_owner_inference_quotas",
        sa.Column("day", sa.String(10), primary_key=True),
        sa.Column("requests", sa.Integer(), nullable=False),
        sa.CheckConstraint("requests >= 0", name="ck_owner_inference_requests"),
    )
    op.create_table(
        "prime_owner_inference_attempts",
        sa.Column("turn_id", sa.Uuid(), primary_key=True),
        sa.Column("day", sa.String(10), sa.ForeignKey("prime_owner_inference_quotas.day"), nullable=False),
        sa.Column("vendor", sa.String(20), nullable=False),
        sa.Column("model", sa.String(160), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("prompt_tokens", sa.Integer()),
        sa.Column("completion_tokens", sa.Integer()),
    )


def downgrade():
    # Retain attempted calls so a rollback does not erase usage evidence.
    pass
