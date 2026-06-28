"""Pack M: Professional Task Lifecycle Engine

Revision ID: 0102_professional_task_links
Revises: 0101_retainer_lifecycle
Create Date: 2025-12-05

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0102_professional_task_links"
down_revision = "0101_retainer_lifecycle"
branch_labels = None
depends_on = None


def upgrade():
    # Create professional_task_links table
    op.create_table(
        "professional_task_links",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("professional_id", sa.Integer, sa.ForeignKey("professionals.id"), nullable=False),
        sa.Column("deal_id", sa.Integer, nullable=False),
        sa.Column("task_id", sa.Integer, nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Create indexes for better query performance
    op.create_index("ix_professional_task_links_professional_id", "professional_task_links", ["professional_id"])
    op.create_index("ix_professional_task_links_deal_id", "professional_task_links", ["deal_id"])
    op.create_index("ix_professional_task_links_task_id", "professional_task_links", ["task_id"])
    op.create_index("ix_professional_task_links_status", "professional_task_links", ["status"])


def downgrade():
    # Drop indexes
    op.drop_index("ix_professional_task_links_status", "professional_task_links")
    op.drop_index("ix_professional_task_links_task_id", "professional_task_links")
    op.drop_index("ix_professional_task_links_deal_id", "professional_task_links")
    op.drop_index("ix_professional_task_links_professional_id", "professional_task_links")

    # Drop table
    op.drop_table("professional_task_links")
