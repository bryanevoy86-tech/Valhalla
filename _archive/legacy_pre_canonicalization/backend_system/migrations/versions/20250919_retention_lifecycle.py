"""
Alembic migration for retention_policies table and export_jobs lifecycle columns (Chunk 46)
"""

import sqlalchemy as sa
from alembic import op

revision = "20250919_retention_lifecycle"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "retention_policies",
        sa.Column(
            "org_id", sa.BigInteger, sa.ForeignKey("orgs.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("retention_days", sa.Integer, nullable=False, server_default=sa.text("30")),
        sa.Column("grace_hours", sa.Integer, nullable=False, server_default=sa.text("24")),
        sa.Column("max_mb", sa.Integer, nullable=False, server_default=sa.text("20480")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("idx_retention_policies_org_id", "retention_policies", ["org_id"], unique=True)

    op.add_column("export_jobs", sa.Column("expires_at", sa.TIMESTAMP(timezone=True)))
    op.add_column("export_jobs", sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)))
    op.add_column("export_jobs", sa.Column("size_bytes", sa.BigInteger))
    op.create_index("idx_export_jobs_finished_at", "export_jobs", ["finished_at"], unique=False)
    op.create_index(
        "idx_export_jobs_org_status_finished",
        "export_jobs",
        ["org_id", "status", "finished_at"],
        unique=False,
    )


def downgrade():
    op.drop_index("idx_retention_policies_org_id", table_name="retention_policies")
    op.drop_table("retention_policies")
    op.drop_index("idx_export_jobs_finished_at", table_name="export_jobs")
    op.drop_index("idx_export_jobs_org_status_finished", table_name="export_jobs")
    op.drop_column("export_jobs", "expires_at")
    op.drop_column("export_jobs", "deleted_at")
    op.drop_column("export_jobs", "size_bytes")
