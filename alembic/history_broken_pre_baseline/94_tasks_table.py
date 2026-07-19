"""Pack 95: add tasks table

Revision ID: 94_tasks_table
Revises: 93_kpi_metrics_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "94_tasks_table"
down_revision = "93_kpi_metrics_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "tasks" not in inspect(bind).get_table_names():
        op.create_table(
            "tasks",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("description", sa.Text()),
            sa.Column("category", sa.String(), server_default=sa.text("'general'")),
            sa.Column("assignee", sa.String(), server_default=sa.text("'king'")),
            sa.Column("status", sa.String(), server_default=sa.text("'pending'")),
            sa.Column("priority", sa.Integer(), server_default=sa.text("'5'")),
            sa.Column("due_at", sa.DateTime()),
            sa.Column("completed_at", sa.DateTime()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("tasks")
