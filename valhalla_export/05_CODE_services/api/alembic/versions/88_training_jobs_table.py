"""Pack 88: add training_jobs table

Revision ID: 88_training_jobs_table
Revises: 87_global_settings_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "88_training_jobs_table"
down_revision = "87_global_settings_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "training_jobs" not in inspect(bind).get_table_names():
        op.create_table(
            "training_jobs",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("job_type", sa.String(), nullable=False),
            sa.Column("target_module", sa.String(), nullable=False),
            sa.Column("status", sa.String(), server_default=sa.text("'pending'")),
            sa.Column("priority", sa.Integer(), server_default="10"),
            sa.Column("progress", sa.Float(), server_default="0.0"),
            sa.Column("payload", sa.Text()),
            sa.Column("error_message", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("started_at", sa.DateTime()),
            sa.Column("finished_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("training_jobs")
