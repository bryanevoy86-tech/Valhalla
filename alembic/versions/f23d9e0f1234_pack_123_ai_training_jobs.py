"""pack_123_ai_training_jobs

Revision ID: f23d9e0f1234
Revises: f22c8d9e0f12
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "f23d9e0f1234"
down_revision = "f22c8d9e0f12"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "ai_training_jobs" not in inspect(bind).get_table_names():
        op.create_table(
            "ai_training_jobs",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("engine_name", sa.String(), nullable=False),
            sa.Column("job_type", sa.String(), nullable=False),
            sa.Column("status", sa.String(), server_default=sa.text("'queued'")),
            sa.Column("started_at", sa.DateTime()),
            sa.Column("finished_at", sa.DateTime()),
            sa.Column("dataset_label", sa.String()),
            sa.Column("epochs", sa.Integer(), server_default=sa.text("0")),
            sa.Column("loss_score", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("quality_score", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("error_message", sa.Text()),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_ai_training_jobs_id", "ai_training_jobs", ["id"], unique=False)
        op.create_index("ix_ai_training_jobs_engine_name", "ai_training_jobs", ["engine_name"], unique=False)
        op.create_index("ix_ai_training_jobs_job_type", "ai_training_jobs", ["job_type"], unique=False)
        op.create_index("ix_ai_training_jobs_status", "ai_training_jobs", ["status"], unique=False)


def downgrade():
    op.drop_index("ix_ai_training_jobs_status", table_name="ai_training_jobs")
    op.drop_index("ix_ai_training_jobs_job_type", table_name="ai_training_jobs")
    op.drop_index("ix_ai_training_jobs_engine_name", table_name="ai_training_jobs")
    op.drop_index("ix_ai_training_jobs_id", table_name="ai_training_jobs")
    op.drop_table("ai_training_jobs")
