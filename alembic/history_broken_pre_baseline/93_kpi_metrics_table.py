"""Pack 94: add kpi_metrics table

Revision ID: 93_kpi_metrics_table
Revises: 92_automation_rules_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "93_kpi_metrics_table"
down_revision = "92_automation_rules_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "kpi_metrics" not in inspect(bind).get_table_names():
        op.create_table(
            "kpi_metrics",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("scope", sa.String(), server_default=sa.text("'empire'")),
            sa.Column("scope_ref", sa.String()),
            sa.Column("period", sa.String(), server_default=sa.text("'month'")),
            sa.Column("period_label", sa.String(), nullable=False),
            sa.Column("value", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("currency", sa.String(), server_default=sa.text("'CAD'")),
            sa.Column("created_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("kpi_metrics")
