"""Pack 99: add error_logs table

Revision ID: 97_error_logs_table
Revises: 96_scheduled_jobs_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "97_error_logs_table"
down_revision = "96_scheduled_jobs_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "error_logs" not in inspect(bind).get_table_names():
        op.create_table(
            "error_logs",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("source", sa.String(), nullable=False),
            sa.Column("location", sa.String()),
            sa.Column("severity", sa.String(), server_default=sa.text("'error'")),
            sa.Column("message", sa.String(), nullable=False),
            sa.Column("stacktrace", sa.Text()),
            sa.Column("context", sa.Text()),
            sa.Column("resolved", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("resolved_note", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("resolved_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("error_logs")
