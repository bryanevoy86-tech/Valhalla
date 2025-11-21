"""add human specialists and case comments

Revision ID: f8dc20521d28
Revises: fa9eb99ebae2
Create Date: 2025-11-21 00:44:24.822767

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f8dc20521d28'
down_revision: Union[str, Sequence[str], None] = 'fa9eb99ebae2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "human_specialists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("role", sa.String(60), nullable=False),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("expertise", postgresql.JSONB, nullable=True),
    )
    
    op.create_table(
        "specialist_case_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("specialist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.ForeignKeyConstraint(["specialist_id"], ["human_specialists.id"]),
        sa.ForeignKeyConstraint(["case_id"], ["god_review_cases.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("specialist_case_comments")
    op.drop_table("human_specialists")
