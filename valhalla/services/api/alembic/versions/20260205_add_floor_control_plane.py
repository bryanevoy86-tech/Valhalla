"""Add floor control plane tables.

Revision ID: 20260205_add_floor_control_plane
Revises: cd7e574386be
Create Date: 2026-02-05
"""
from alembic import op
import sqlalchemy as sa

revision = "20260205_add_floor_control_plane"
down_revision = "cd7e574386be"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "income_engines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="DESIGNED"),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sandbox_only", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("code", name="uq_income_engines_code"),
    )

    op.create_table(
        "revenue_ledger",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("engine_code", sa.String(), nullable=False),
        sa.Column("source_ref", sa.String(), nullable=True),
        sa.Column("currency", sa.String(), nullable=False, server_default="USD"),
        sa.Column("gross_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("fun_fund_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("reinvest_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("ops_reserve_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_revenue_ledger_engine_date", "revenue_ledger", ["engine_code", "as_of_date"])

    op.create_table(
        "trajectory_targets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("engine_code", sa.String(), nullable=False, server_default="SYSTEM"),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False, server_default="USD"),
        sa.Column("min_gross", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("min_fun_fund", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("engine_code", "month", name="uq_targets_engine_month"),
    )

    op.create_table(
        "engine_activation_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("engine_code", sa.String(), nullable=False),
        sa.Column("min_monthly_gross", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("min_success_rate", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("max_risk_score", sa.Numeric(6, 3), nullable=False, server_default="1"),
        sa.Column("require_contracts_ready", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("require_compliance_ready", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("require_payment_rails_ready", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("engine_code", name="uq_engine_activation_rules_engine_code"),
    )

def downgrade():
    op.drop_table("engine_activation_rules")
    op.drop_table("trajectory_targets")
    op.drop_index("ix_revenue_ledger_engine_date", table_name="revenue_ledger")
    op.drop_table("revenue_ledger")
    op.drop_table("income_engines")
