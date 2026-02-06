"""
Alembic migration: Create cron_runs and related tables.

This migration creates tables for:
- cron_runs: Track cron job executions
- cron_results: Store cron job results
- system_events: General system events
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "20260205_ops_and_events"
down_revision = "20260205_final_consolidation"
branch_labels = None
depends_on = None


def upgrade():
    """Create cron and events tables."""
    
    # Create cron_runs table
    op.create_table(
        "cron_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),  # success, error, running
        sa.Column("started_at", sa.TIMESTAMP, nullable=False),
        sa.Column("completed_at", sa.TIMESTAMP, nullable=True),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("idx_cron_runs_job_name", "cron_runs", ["job_name"])
    op.create_index("idx_cron_runs_started_at", "cron_runs", ["started_at"])
    
    # Create cron_results table
    op.create_table(
        "cron_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("cron_run_id", sa.String(length=36), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["cron_run_id"], ["cron_runs.id"])
    )
    op.create_index("idx_cron_results_cron_run_id", "cron_results", ["cron_run_id"])
    
    # Create system_events table for audit trail
    op.create_table(
        "system_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),  # activation, error, warning, info
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("severity", sa.String(length=10), nullable=False),  # critical, high, medium, low, info
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("idx_system_events_event_type", "system_events", ["event_type"])
    op.create_index("idx_system_events_created_at", "system_events", ["created_at"])


def downgrade():
    """Drop cron and events tables."""
    op.drop_index("idx_system_events_created_at", table_name="system_events")
    op.drop_index("idx_system_events_event_type", table_name="system_events")
    op.drop_table("system_events")
    
    op.drop_index("idx_cron_results_cron_run_id", table_name="cron_results")
    op.drop_table("cron_results")
    
    op.drop_index("idx_cron_runs_started_at", table_name="cron_runs")
    op.drop_index("idx_cron_runs_job_name", table_name="cron_runs")
    op.drop_table("cron_runs")
