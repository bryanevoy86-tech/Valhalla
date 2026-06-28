"""Pack 98: add scheduled_jobs table

Revision ID: 96_scheduled_jobs_table
Revises: 95_automation_runs_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "96_scheduled_jobs_table"
down_revision = "95_automation_runs_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "scheduled_jobs" not in inspect(bind).get_table_names():
        op.create_table(
            "scheduled_jobs",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("category", sa.String(), server_default=sa.text("'general'")),
            sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("schedule", sa.String(), nullable=False),
            sa.Column("task_path", sa.String(), nullable=False),
            sa.Column("args", sa.Text()),
            sa.Column("last_run_at", sa.DateTime()),
            sa.Column("last_status", sa.String()),
            sa.Column("last_error", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("scheduled_jobs")
