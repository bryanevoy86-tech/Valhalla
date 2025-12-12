"""Pack 114: add system_health_reports table

Revision ID: 107_system_health_reports_table
Revises: 0114
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "107_system_health_reports_table"
down_revision = "0114"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "system_health_reports" not in inspect(bind).get_table_names():
        op.create_table(
            "system_health_reports",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("run_at", sa.DateTime()),
            sa.Column("period_label", sa.String(), nullable=False),
            sa.Column("errors_count", sa.Integer(), server_default=sa.text("0")),
            sa.Column("critical_errors", sa.Integer(), server_default=sa.text("0")),
            sa.Column("failed_automations", sa.Integer(), server_default=sa.text("0")),
            sa.Column("unresolved_compliance_signals", sa.Integer(), server_default=sa.text("0")),
            sa.Column("all_green", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("summary", sa.Text()),
            sa.Column("notes", sa.Text()),
        )


def downgrade():
    op.drop_table("system_health_reports")
