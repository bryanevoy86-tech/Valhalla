"""Create KPI Event, Regression Policy, Regression State tables with seed policies."""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = "20260113_regression_tripwire"
down_revision = "20260113_heimdall_charter"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # KPIEvent table: business metrics recording
    op.create_table(
        "kpi_event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain", sa.String(32), nullable=False),
        sa.Column("metric", sa.String(64), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("actor", sa.String(64), nullable=True),
        sa.Column("correlation_id", sa.String(128), nullable=True),
        sa.Column("detail", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    # Index for query performance: recent events per (domain, metric)
    op.create_index("ix_kpi_event_domain_metric_created", "kpi_event", ["domain", "metric", "created_at"])

    # RegressionPolicy table: per-(domain, metric) regression thresholds
    op.create_table(
        "regression_policy",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain", sa.String(32), nullable=False),
        sa.Column("metric", sa.String(64), nullable=False),
        sa.Column("window_events", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("baseline_events", sa.Integer(), nullable=False, server_default="200"),
        sa.Column("min_events_to_enforce", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("max_drop_fraction", sa.Float(), nullable=False, server_default="0.20"),
        sa.Column("action", sa.String(32), nullable=False, server_default="THROTTLE"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("changed_by", sa.String(64), nullable=True),
        sa.Column("reason", sa.String(512), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain", "metric", name="ux_regression_policy_domain_metric"),
    )

    # RegressionState table: current tripwire status
    op.create_table(
        "regression_state",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain", sa.String(32), nullable=False),
        sa.Column("metric", sa.String(64), nullable=False),
        sa.Column("triggered", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("baseline", sa.Float(), nullable=True),
        sa.Column("current", sa.Float(), nullable=True),
        sa.Column("drop_fraction", sa.Float(), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
        sa.Column("last_triggered_at", sa.DateTime(), nullable=True),
        sa.Column("note", sa.String(512), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain", "metric", name="ux_regression_state_domain_metric"),
    )

    # Seed 4 regression policies
    now = datetime.utcnow()
    op.execute(
        f"""
        INSERT INTO regression_policy
        (domain, metric, window_events, baseline_events, min_events_to_enforce, max_drop_fraction, action, enabled, changed_by, reason, updated_at)
        VALUES
        ('WHOLESALE', 'contract_rate', 50, 200, 50, 0.20, 'THROTTLE', false, 'system', 'Contracts accepted %', '{now}'),
        ('WHOLESALE', 'offer_accept_rate', 50, 200, 50, 0.15, 'THROTTLE', false, 'system', 'Offers accepted %', '{now}'),
        ('BUYER_MATCH', 'match_success', 50, 200, 50, 0.25, 'THROTTLE', false, 'system', 'Buyer match success %', '{now}'),
        ('CAPITAL', 'roi_event', 50, 200, 50, 0.30, 'KILL_SWITCH', false, 'system', 'Capital ROI %', '{now}')
        """
    )


def downgrade() -> None:
    op.drop_table("regression_state")
    op.drop_table("regression_policy")
    op.drop_index("ix_kpi_event_domain_metric_created", table_name="kpi_event")
    op.drop_table("kpi_event")
