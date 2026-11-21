"""Add private owner conversation storage without changing existing records."""
from alembic import op
import sqlalchemy as sa

revision = "20261120_owner_conversation"
down_revision = "20261120_product_artifacts"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("prime_owner_conversations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("prime_owner_turns",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("conversation_id", sa.Uuid(), sa.ForeignKey("prime_owner_conversations.id"), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("reply", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("attachment_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_prime_owner_turn_thread", "prime_owner_turns", ["conversation_id", "created_at"])
    op.create_table("prime_owner_attachments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("conversation_id", sa.Uuid(), sa.ForeignKey("prime_owner_conversations.id"), nullable=False),
        sa.Column("filename", sa.String(180), nullable=False),
        sa.Column("media_type", sa.String(100), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(data) BETWEEN 1 AND 5242880", name="ck_prime_owner_attachment_size"))
    op.create_index("ix_prime_owner_attachment_thread", "prime_owner_attachments", ["conversation_id"])

def downgrade():
    # Preserve uploaded evidence and conversation history on code rollback.
    pass
