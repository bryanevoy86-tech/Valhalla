"""ci1_add_decision_recommendations

Revision ID: ci1_add_decision_recommendations
Revises: 0077
Create Date: 2024-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "ci1_add_decision_recommendations"
down_revision = "0077"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "decision_context_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False),
        sa.Column("context_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "decision_recommendations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("context_id", sa.Integer(), nullable=False, index=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("leverage_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("urgency_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("alignment_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("priority_rank", sa.Integer(), nullable=False, server_default="999"),
        sa.Column("recommended", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("decision_recommendations")
    op.drop_table("decision_context_snapshots")
