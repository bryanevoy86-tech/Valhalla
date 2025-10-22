"""v3.1 - metrics & capital_intake tables

Revision ID: v3_1_metrics_capital
Revises: 
Create Date: 2025-10-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "v3_1_metrics_capital"
down_revision = "ops_enablers_001"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    insp = inspect(bind)
    existing_tables = set(insp.get_table_names())

    # Create metrics only if missing
    if "metrics" not in existing_tables:
        op.create_table(
            "metrics",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(length=100), nullable=False, index=True),
            sa.Column("value", sa.Float, nullable=False),
            sa.Column("unit", sa.String(length=32), nullable=True),
            sa.Column("tags", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        )
        op.create_index("ix_metrics_name", "metrics", ["name"])

    # Create capital_intake only if missing
    if "capital_intake" not in existing_tables:
        op.create_table(
            "capital_intake",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("source", sa.String(length=100), nullable=False),
            sa.Column("amount", sa.Numeric(18, 2), nullable=False),
            sa.Column("currency", sa.String(length=10), nullable=False, server_default="CAD"),
            sa.Column("note", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        )

def downgrade():
    bind = op.get_bind()
    insp = inspect(bind)
    existing_tables = set(insp.get_table_names())

    if "capital_intake" in existing_tables:
        op.drop_table("capital_intake")

    if "metrics" in existing_tables:
        metrics_indexes = {idx.get("name") for idx in insp.get_indexes("metrics")}
        if "ix_metrics_name" in metrics_indexes:
            op.drop_index("ix_metrics_name", table_name="metrics")
        op.drop_table("metrics")
