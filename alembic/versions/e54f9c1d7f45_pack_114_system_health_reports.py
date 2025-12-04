"""pack_114_system_health_reports

Revision ID: e54f9c1d7f45
Revises: d43f8b0c6e34
Create Date: 2025-11-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "e54f9c1d7f45"
down_revision: Union[str, Sequence[str], None] = "d43f8b0c6e34"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "system_health_reports" not in insp.get_table_names():
        op.create_table(
            "system_health_reports",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("run_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("period_label", sa.String(), nullable=False),
            sa.Column("errors_count", sa.Integer(), server_default=sa.text("0")),
            sa.Column("critical_errors", sa.Integer(), server_default=sa.text("0")),
            sa.Column("failed_automations", sa.Integer(), server_default=sa.text("0")),
            sa.Column("unresolved_compliance_signals", sa.Integer(), server_default=sa.text("0")),
            sa.Column("all_green", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("summary", sa.Text()),
            sa.Column("notes", sa.Text()),
        )
        op.create_index("ix_system_health_reports_id", "system_health_reports", ["id"], unique=False)
        op.create_index("ix_system_health_reports_period_label", "system_health_reports", ["period_label"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_system_health_reports_period_label", table_name="system_health_reports")
    op.drop_index("ix_system_health_reports_id", table_name="system_health_reports")
    op.drop_table("system_health_reports")
