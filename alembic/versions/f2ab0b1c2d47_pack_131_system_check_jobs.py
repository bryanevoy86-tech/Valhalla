"""pack_131_system_check_jobs

Revision ID: f2ab0b1c2d47
Revises: f2aa0b1c2d46
Create Date: 2025-11-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "f2ab0b1c2d47"
down_revision: Union[str, Sequence[str], None] = "f2aa0b1c2d46"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "system_check_jobs" not in inspector.get_table_names():
        op.create_table(
            "system_check_jobs",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("scope", sa.String(), nullable=False),
            sa.Column("scope_code", sa.String()),
            sa.Column("schedule", sa.String(), server_default="weekly"),
            sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("last_run_at", sa.DateTime()),
            sa.Column("last_status", sa.String()),
            sa.Column("last_health_score", sa.Float(), server_default="1.0"),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )
        op.create_index("ix_system_check_jobs_scope", "system_check_jobs", ["scope"])
        op.create_index("ix_system_check_jobs_active", "system_check_jobs", ["active"])


def downgrade() -> None:
    op.drop_index("ix_system_check_jobs_active", table_name="system_check_jobs")
    op.drop_index("ix_system_check_jobs_scope", table_name="system_check_jobs")
    op.drop_table("system_check_jobs")
