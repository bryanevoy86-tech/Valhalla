"""v3.2 - builder tasks & events

Revision ID: v3_2_builder
Revises: v3_1_metrics_capital
Create Date: 2025-10-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "v3_2_builder"
down_revision = "v3_1_metrics_capital"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    insp = inspect(bind)
    existing_tables = set(insp.get_table_names())

    # Create builder_tasks only if missing
    if "builder_tasks" not in existing_tables:
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
    
    # Create builder_events only if missing
    if "builder_events" not in existing_tables:
        op.create_table(
            "builder_events",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("kind", sa.String(length=40), nullable=False),
            sa.Column("msg", sa.Text, nullable=True),
            sa.Column("meta_json", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        )

def downgrade():
    bind = op.get_bind()
    insp = inspect(bind)
    existing_tables = set(insp.get_table_names())

    if "builder_events" in existing_tables:
        op.drop_table("builder_events")
    if "builder_tasks" in existing_tables:
        op.drop_table("builder_tasks")
