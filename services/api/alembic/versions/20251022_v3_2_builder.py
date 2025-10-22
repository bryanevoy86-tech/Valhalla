"""v3.2 - builder tasks & events

Revision ID: v3_2_builder
Revises: v3_1_metrics_capital
Create Date: 2025-10-22
"""
from alembic import op
import sqlalchemy as sa

revision = "v3_2_builder"
down_revision = "v3_1_metrics_capital"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "builder_tasks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(length=140), nullable=False),
        sa.Column("scope", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("plan", sa.Text, nullable=True),
        sa.Column("diff_summary", sa.Text, nullable=True),
        sa.Column("payload_json", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "builder_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("msg", sa.Text, nullable=True),
        sa.Column("meta_json", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

def downgrade():
    op.drop_table("builder_events")
    op.drop_table("builder_tasks")
