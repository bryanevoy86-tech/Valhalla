from alembic import op
import sqlalchemy as sa

revision = "0046_clone_mirror_policies"
down_revision = "0045_deal_doc_templates_send"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "policy_gate_metrics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("uptime_pct", sa.Float, nullable=False),
        sa.Column("cash_reserves", sa.Numeric(14, 2), nullable=False),
        sa.Column("net_margin_pct", sa.Float, nullable=False),
        sa.Column("audit_score", sa.Float, nullable=False),
        sa.Column("error_rate_ppm", sa.Integer, nullable=False),
        sa.Column("traffic_p90_rps", sa.Float, nullable=True),
        sa.Column("latency_p95_ms", sa.Float, nullable=True),
    )
    op.create_table(
        "clone_policies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("min_days_between", sa.Integer, nullable=False),
        sa.Column("max_active", sa.Integer, nullable=False),
        sa.Column("required_uptime_pct", sa.Float, nullable=False),
        sa.Column("required_cash_reserves", sa.Numeric(14, 2), nullable=False),
        sa.Column("required_net_margin_pct", sa.Float, nullable=False),
        sa.Column("required_audit_score", sa.Float, nullable=False),
        sa.Column("max_error_rate_ppm", sa.Integer, nullable=False),
        sa.Column("last_triggered_at", sa.DateTime, nullable=True),
    )
    op.create_table(
        "mirror_policies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("min_days_between", sa.Integer, nullable=False),
        sa.Column("max_active", sa.Integer, nullable=False),
        sa.Column("required_p90_rps", sa.Float, nullable=False),
        sa.Column("required_p95_latency_ms", sa.Float, nullable=False),
        sa.Column("last_triggered_at", sa.DateTime, nullable=True),
    )
    op.create_table(
        "policy_event_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("snapshot_json", sa.Text, nullable=False),
    )


def downgrade():
    op.drop_table("policy_event_logs")
    op.drop_table("mirror_policies")
    op.drop_table("clone_policies")
    op.drop_table("policy_gate_metrics")
