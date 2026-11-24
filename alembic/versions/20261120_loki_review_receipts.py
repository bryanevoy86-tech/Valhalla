"""Persist independent review evidence and owner reconsideration."""

from alembic import op
import sqlalchemy as sa

revision = "20261120_loki_review_receipts"
down_revision = "20261120_buyer_claim_expiry"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("loki_reviews", sa.Column("artifact_sha256", sa.String(64), nullable=True))
    op.create_index("uq_loki_reviews_artifact_sha256", "loki_reviews", ["artifact_sha256"], unique=True)
    op.create_table(
        "loki_independent_receipts",
        sa.Column("review_id", sa.Uuid(), sa.ForeignKey("loki_reviews.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("artifact_sha256", sa.String(64), nullable=False),
        sa.Column("reviewer_id", sa.String(100), nullable=False),
        sa.Column("analysis_ref", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "loki_reconsiderations",
        sa.Column("review_id", sa.Uuid(), sa.ForeignKey("loki_independent_receipts.review_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("artifact_sha256", sa.String(64), nullable=False),
        sa.Column("disposition", sa.String(24), nullable=False),
        sa.Column("material_finding_ids", sa.JSON(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    # Preserve decision evidence when rolling the application version back.
    pass
