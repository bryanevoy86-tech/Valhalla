"""add progress columns and index to export_jobs

Revision ID: 20250919_add_progress_cols
Revises: <PUT_PREVIOUS_REVISION_ID_HERE>
Create Date: 2025-09-19

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20250919_add_progress_cols"
down_revision = "<PUT_PREVIOUS_REVISION_ID_HERE>"
branch_labels = None
depends_on = None


def upgrade():
    # columns
    op.add_column(
        "export_jobs",
        sa.Column("progress", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column("export_jobs", sa.Column("progress_msg", sa.Text(), nullable=True))
    op.add_column(
        "export_jobs",
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "export_jobs",
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )

    # composite index (status, created_at desc)
    # alembic's Index API doesn't express DESC per-column portably; this is fine:
    op.create_index(
        "idx_export_jobs_status_created",
        "export_jobs",
        ["status", "created_at"],
        unique=False,
    )


def downgrade():
    # drop index
    op.drop_index("idx_export_jobs_status_created", table_name="export_jobs")
    # drop columns
    for col in ["finished_at", "started_at", "progress_msg", "progress"]:
        op.drop_column("export_jobs", col)
