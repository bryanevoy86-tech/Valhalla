"""0076 pack uh export jobs

Revision ID: 0076
Revises: 0075
Create Date: 2024-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0076"
down_revision = "0075"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "export_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("job_type", sa.String(128), nullable=False),
        sa.Column("filter_params", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(32), default="pending", nullable=False),
        sa.Column("storage_url", sa.String(512), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("requested_by", sa.String(256), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_export_jobs_status", "export_jobs", ["status"])
    op.create_index("idx_export_jobs_created", "export_jobs", ["created_at"])


def downgrade() -> None:
    op.drop_table("export_jobs")
