"""pack_133_expert_reviews

Revision ID: f2ad0b1c2d49
Revises: f2ac0b1c2d48
Create Date: 2025-11-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "f2ad0b1c2d49"
down_revision: Union[str, Sequence[str], None] = "f2ac0b1c2d48"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "expert_reviews" not in inspector.get_table_names():
        op.create_table(
            "expert_reviews",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("expert_id", sa.Integer(), nullable=False),
            sa.Column("topic", sa.String(), nullable=False),
            sa.Column("domain", sa.String(), nullable=False),
            sa.Column("heimdall_recommendation", sa.Text()),
            sa.Column("expert_recommendation", sa.Text()),
            sa.Column("alignment_score", sa.Float(), server_default="1.0"),
            sa.Column("action_taken", sa.Text()),
            sa.Column("meeting_date", sa.DateTime(), nullable=False),
            sa.Column("recording_url", sa.String()),
            sa.Column("created_at", sa.DateTime()),
        )
        op.create_index("ix_expert_reviews_domain", "expert_reviews", ["domain"])
        op.create_index("ix_expert_reviews_expert_id", "expert_reviews", ["expert_id"])


def downgrade() -> None:
    op.drop_index("ix_expert_reviews_expert_id", table_name="expert_reviews")
    op.drop_index("ix_expert_reviews_domain", table_name="expert_reviews")
    op.drop_table("expert_reviews")
