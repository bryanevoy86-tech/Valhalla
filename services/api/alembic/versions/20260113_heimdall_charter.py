"""heimdall confidence charter tables

Revision ID: 20260113_heimdall_charter
Revises: 20260113_risk_floors
Create Date: 2026-01-13
"""

from alembic import op
import sqlalchemy as sa

revision = "20260113_heimdall_charter"
down_revision = "20260113_risk_floors"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "heimdall_policy",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("min_confidence_prod", sa.Float(), nullable=False, server_default=sa.text("0.90")),
        sa.Column("min_sandbox_trials", sa.Integer(), nullable=False, server_default=sa.text("50")),
        sa.Column("min_sandbox_success_rate", sa.Float(), nullable=False, server_default=sa.text("0.80")),
        sa.Column("prod_use_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("changed_by", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("domain", name="uq_heimdall_policy_domain"),
    )

    op.create_table(
        "heimdall_scorecard_day",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("trials", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("successes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("success_rate", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("avg_confidence", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("day", "domain", name="uq_heimdall_scorecard_day_domain"),
    )

    op.create_table(
        "heimdall_recommendation",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("recommendation_json", sa.Text(), nullable=False),
        sa.Column("evidence_json", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(), nullable=True),
        sa.Column("actor", sa.String(), nullable=True),
        sa.Column("prod_eligible", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("gate_reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "heimdall_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("event", sa.String(), nullable=False),
        sa.Column("ok", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("recommendation_id", sa.Integer(), nullable=True),
        sa.Column("correlation_id", sa.String(), nullable=True),
        sa.Column("actor", sa.String(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # Seed conservative defaults (prod use OFF until you explicitly enable)
    op.execute(
        "INSERT INTO heimdall_policy (domain, min_confidence_prod, min_sandbox_trials, min_sandbox_success_rate, prod_use_enabled, changed_by, reason, updated_at) VALUES "
        "('WHOLESALE_OFFER', 0.92, 75, 0.82, 0, 'system', 'Seed charter policy', CURRENT_TIMESTAMP),"
        "('BUYER_MATCH', 0.90, 50, 0.80, 0, 'system', 'Seed charter policy', CURRENT_TIMESTAMP),"
        "('CAPITAL_ROUTE', 0.95, 100, 0.85, 0, 'system', 'Seed charter policy', CURRENT_TIMESTAMP),"
        "('FOLLOWUP_NEXT_ACTION', 0.90, 60, 0.80, 0, 'system', 'Seed charter policy', CURRENT_TIMESTAMP)"
    )


def downgrade():
    op.drop_table("heimdall_event")
    op.drop_table("heimdall_recommendation")
    op.drop_table("heimdall_scorecard_day")
    op.drop_table("heimdall_policy")
