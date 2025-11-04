"""
Alembic migration for jobs worker tables
"""

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, index=True),
        sa.Column("name", sa.String, nullable=False, index=True),
        sa.Column("args", sa.JSON),
        sa.Column("status", sa.String, nullable=False, server_default="queued"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="5"),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer, nullable=False, server_default="3"),
        sa.Column(
            "scheduled_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("progress", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_error", sa.String),
        sa.Column("created_by", sa.Integer, index=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
    )
    op.create_table(
        "job_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "job_id",
            sa.Integer,
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column(
            "started_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("success", sa.Boolean, server_default=sa.text("0"), index=True),
        sa.Column("error", sa.String),
        sa.Column("logs", sa.JSON),
    )
    op.create_table(
        "dist_locks",
        sa.Column("key", sa.String, primary_key=True),
        sa.Column("owner", sa.String, nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), index=True),
    )


def downgrade():
    op.drop_table("dist_locks")
    op.drop_table("job_runs")
    op.drop_table("jobs")
