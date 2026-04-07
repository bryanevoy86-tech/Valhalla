"""ci4_add_insights

Revision ID: ci4_add_insights
Revises: ci3_add_trajectory
Create Date: 2024-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "ci4_add_insights"
down_revision = "ci3_add_trajectory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "insights",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("importance", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("insights")
