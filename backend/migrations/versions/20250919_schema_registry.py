"""
Alembic migration for export_schema_versions registry and export_jobs schema_version pins (Chunk 47)
"""

import sqlalchemy as sa
from alembic import op

revision = "20250919_schema_registry"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "export_schema_versions",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("job_type", sa.String(64), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("schema", sa.JSON, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.UniqueConstraint("job_type", "version", name="uq_schema_jobtype_version"),
    )
    op.create_index(
        "idx_schema_versions_jobtype",
        "export_schema_versions",
        ["job_type", "version"],
        unique=False,
    )

    op.add_column("export_jobs", sa.Column("schema_version", sa.Integer))
    op.add_column("export_jobs", sa.Column("schema_errors", sa.JSON))


def downgrade():
    op.drop_index("idx_schema_versions_jobtype", table_name="export_schema_versions")
    op.drop_table("export_schema_versions")
    op.drop_column("export_jobs", "schema_version")
    op.drop_column("export_jobs", "schema_errors")
