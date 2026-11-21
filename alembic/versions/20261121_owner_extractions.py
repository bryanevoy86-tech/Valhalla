"""Retain bounded local extraction and source hashes."""
from alembic import op
import sqlalchemy as sa

revision = "20261121_owner_extractions"
down_revision = "20261121_owner_memory"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_owner_attachment_extractions",
        sa.Column("attachment_id", sa.Uuid(), sa.ForeignKey("prime_owner_attachments.id"), primary_key=True),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    # Preserve extraction provenance during rollback.
    pass
