import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20250918_export_retry"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "export_jobs", sa.Column("attempts", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "export_jobs", sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3")
    )
    op.add_column("export_jobs", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column(
        "export_jobs",
        sa.Column("next_run_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.add_column(
        "export_jobs",
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
    )
    op.add_column(
        "export_jobs",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.add_column(
        "export_jobs",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index(
        "idx_export_jobs_created_at",
        "export_jobs",
        ["created_at"],
        unique=False,
        postgresql_sort="DESC",
    )
    op.create_index(
        "idx_export_jobs_status_next_run", "export_jobs", ["status", "next_run_at"], unique=False
    )


def downgrade():
    op.drop_index("idx_export_jobs_status_next_run", table_name="export_jobs")
    op.drop_index("idx_export_jobs_created_at", table_name="export_jobs")
    for col in [
        "attempts",
        "max_attempts",
        "last_error",
        "next_run_at",
        "status",
        "created_at",
        "updated_at",
    ]:
        op.drop_column("export_jobs", col)
