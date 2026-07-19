"""Pack 96: add automation_runs table

Revision ID: 95_automation_runs_table
Revises: 94_tasks_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "95_automation_runs_table"
down_revision = "94_tasks_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "automation_runs" not in inspect(bind).get_table_names():
        op.create_table(
            "automation_runs",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("rule_id", sa.Integer(), nullable=False),
            sa.Column("rule_name", sa.String(), nullable=False),
            sa.Column("status", sa.String(), server_default=sa.text("'started'")),
            sa.Column("severity", sa.String(), server_default=sa.text("'info'")),
            sa.Column("input_snapshot", sa.Text()),
            sa.Column("action_result", sa.Text()),
            sa.Column("error_message", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("finished_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("automation_runs")
