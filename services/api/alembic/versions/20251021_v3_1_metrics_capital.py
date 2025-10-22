"""v3.1 - metrics & capital_intake tables

Revision ID: v3_1_metrics_capital
Revises: 
Create Date: 2025-10-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "v3_1_metrics_capital"
down_revision = "ops_enablers_001"
branch_labels = None
depends_on = None

def upgrade():
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
    op.drop_table("capital_intake")
    op.drop_index("ix_metrics_name", table_name="metrics")
    op.drop_table("metrics")
