"""risk floors tables

Revision ID: 20260113_risk_floors
Revises: 20260113_golive_merge
Create Date: 2026-01-13
"""

from alembic import op
import sqlalchemy as sa

revision = "20260113_risk_floors"
down_revision = "20260113_golive_merge"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "risk_policy",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("engine", sa.String(), nullable=False),
        sa.Column("max_daily_loss", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("max_daily_exposure", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("max_open_risk", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("max_actions_per_day", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("changed_by", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("engine", name="uq_risk_policy_engine"),
    )

    op.create_table(
        "risk_ledger_day",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("engine", sa.String(), nullable=False),
        sa.Column("exposure_used", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("open_risk_reserved", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("realized_loss", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("actions_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("day", "engine", name="uq_risk_ledger_day_engine"),
    )

    op.create_table(
        "risk_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("engine", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("ok", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("correlation_id", sa.String(), nullable=True),
        sa.Column("actor", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # Seed conservative policies (safe defaults)
    op.execute(
        "INSERT INTO risk_policy (engine, max_daily_loss, max_daily_exposure, max_open_risk, max_actions_per_day, enabled, changed_by, reason, updated_at) "
        "VALUES "
        "('GLOBAL', 250.0, 1500.0, 1500.0, 0, 1, 'system', 'Seed default GLOBAL floors', CURRENT_TIMESTAMP),"
        "('WHOLESALE', 200.0, 1000.0, 1000.0, 0, 1, 'system', 'Seed default WHOLESALE floors', CURRENT_TIMESTAMP),"
        "('CAPITAL', 150.0, 750.0, 750.0, 0, 1, 'system', 'Seed default CAPITAL floors', CURRENT_TIMESTAMP),"
        "('NOTIFY', 0.0, 0.0, 0.0, 0, 0, 'system', 'Disabled until comms policies are set', CURRENT_TIMESTAMP)"
    )


def downgrade():
    op.drop_table("risk_event")
    op.drop_table("risk_ledger_day")
    op.drop_table("risk_policy")
