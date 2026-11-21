"""Persist scoped, sourced owner memory without promoting claims to facts."""
from alembic import op
import sqlalchemy as sa

revision = "20261121_owner_memory"
down_revision = "20261121_owner_inference_limits"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prime_owner_memory_entries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("conversation_id", sa.Uuid(), sa.ForeignKey("prime_owner_conversations.id"), nullable=False),
        sa.Column("source_turn_id", sa.Uuid(), sa.ForeignKey("prime_owner_turns.id"), nullable=False),
        sa.Column("supersedes_id", sa.Uuid(), sa.ForeignKey("prime_owner_memory_entries.id"), unique=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("visibility", sa.String(20), nullable=False),
        sa.Column("topic", sa.String(120), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_prime_owner_memory_scope", "prime_owner_memory_entries", ["conversation_id", "visibility", "created_at"],
    )


def downgrade():
    # Memory and source evidence survive application rollback.
    pass
