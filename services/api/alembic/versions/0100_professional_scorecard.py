"""Pack J: Professional Scorecard Engine

Revision ID: 0100_professional_scorecard
Revises: 99_funfund_routing_table
Create Date: 2025-12-05

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0100_professional_scorecard"
down_revision = "0067"
branch_labels = None
depends_on = None


def upgrade():
    # Create professionals table
    op.create_table(
        "professionals",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("role", sa.String(100), nullable=False),
        sa.Column("organization", sa.String(200), nullable=True),
        sa.Column("public_urls", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Create professional_interactions table
    op.create_table(
        "professional_interactions",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("professional_id", sa.Integer, sa.ForeignKey("professionals.id"), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("response_time_hours", sa.Float, nullable=True),
        sa.Column("deliverable_quality", sa.Float, nullable=True),
        sa.Column("communication_clarity", sa.Float, nullable=True),
        sa.Column("met_deadline", sa.Integer, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
    )

    # Create professional_scorecards table
    op.create_table(
        "professional_scorecards",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("professional_id", sa.Integer, sa.ForeignKey("professionals.id"), nullable=False, unique=True),
        sa.Column("reliability_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("communication_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("quality_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("overall_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Create indexes for better query performance
    op.create_index("ix_professionals_role", "professionals", ["role"])
    op.create_index("ix_professional_interactions_professional_id", "professional_interactions", ["professional_id"])
    op.create_index("ix_professional_scorecards_overall_score", "professional_scorecards", ["overall_score"])


def downgrade():
    # Drop indexes
    op.drop_index("ix_professional_scorecards_overall_score", "professional_scorecards")
    op.drop_index("ix_professional_interactions_professional_id", "professional_interactions")
    op.drop_index("ix_professionals_role", "professionals")

    # Drop tables in reverse order (to respect foreign keys)
    op.drop_table("professional_scorecards")
    op.drop_table("professional_interactions")
    op.drop_table("professionals")
