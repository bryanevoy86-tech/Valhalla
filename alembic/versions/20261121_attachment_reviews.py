"""Record owner disposition of private uploaded evidence."""
from alembic import op
import sqlalchemy as sa

revision = "20261121_attachment_reviews"
down_revision = "20261121_norns_scoped_history"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_owner_attachment_reviews",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("attachment_id", sa.Uuid(), sa.ForeignKey("prime_owner_attachments.id"), nullable=False),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("disposition", sa.String(24), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prime_owner_attachment_reviews_attachment_id", "prime_owner_attachment_reviews", ["attachment_id"])


def downgrade():
    # Preserve dispositions and their provenance.
    pass
