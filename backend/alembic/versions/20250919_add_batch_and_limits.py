"""add batch and limits columns/tables to export_jobs

Revision ID: 20250919_add_batch_and_limits
Revises: 20250919_add_progress_cols
Create Date: 2025-09-19

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20250919_add_batch_and_limits"
down_revision = "20250919_add_progress_cols"
branch_labels = None
depends_on = None


def upgrade():
    # export_jobs columns
    op.add_column(
        "export_jobs",
        sa.Column("org_id", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )
    op.add_column("export_jobs", sa.Column("batch_id", sa.Integer(), nullable=True))
    op.add_column(
        "export_jobs",
        sa.Column("priority", sa.Integer(), nullable=False, server_default=sa.text("100")),
    )

    # export_batches table
    op.create_table(
        "export_batches",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(160), nullable=True),
        sa.Column("job_type", sa.String(64), nullable=False),
        sa.Column("params_template", sa.JSON(), nullable=True),
        sa.Column("total_jobs", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("enqueued_jobs", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # export_limits table
    op.create_table(
        "export_limits",
        sa.Column("org_id", sa.Integer(), primary_key=True),
        sa.Column("max_concurrent", sa.Integer(), nullable=False, server_default=sa.text("2")),
        sa.Column("daily_quota", sa.Integer(), nullable=False, server_default=sa.text("2000")),
    )

    # indexes
    op.create_index("idx_export_jobs_batch", "export_jobs", ["batch_id"], unique=False)
    op.create_index(
        "idx_export_jobs_org_status",
        "export_jobs",
        ["org_id", "status", "next_run_at"],
        unique=False,
    )


def downgrade():
    op.drop_index("idx_export_jobs_batch", table_name="export_jobs")
    op.drop_index("idx_export_jobs_org_status", table_name="export_jobs")
    op.drop_table("export_batches")
    op.drop_table("export_limits")
    for col in ["priority", "batch_id", "org_id"]:
        op.drop_column("export_jobs", col)
