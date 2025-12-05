"""Pack K: Retainer Lifecycle Engine

Revision ID: 0101_retainer_lifecycle
Revises: 0100_professional_scorecard
Create Date: 2025-12-05

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0101_retainer_lifecycle"
down_revision = "0100_professional_scorecard"
branch_labels = None
depends_on = None


def upgrade():
    # Create retainers table
    op.create_table(
        "retainers",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("professional_id", sa.Integer, sa.ForeignKey("professionals.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("monthly_hours_included", sa.Float, nullable=False),
        sa.Column("hourly_rate", sa.Float, nullable=True),
        sa.Column("renewal_date", sa.Date, nullable=False),
        sa.Column("hours_used", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Create indexes for better query performance
    op.create_index("ix_retainers_professional_id", "retainers", ["professional_id"])
    op.create_index("ix_retainers_is_active", "retainers", ["is_active"])
    op.create_index("ix_retainers_renewal_date", "retainers", ["renewal_date"])


def downgrade():
    # Drop indexes
    op.drop_index("ix_retainers_renewal_date", "retainers")
    op.drop_index("ix_retainers_is_active", "retainers")
    op.drop_index("ix_retainers_professional_id", "retainers")

    # Drop table
    op.drop_table("retainers")
