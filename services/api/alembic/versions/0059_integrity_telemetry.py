"""Pack 59: Integrity Ledger + Telemetry Finalization"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
import logging

revision = "0059_integrity_telemetry"
down_revision = "0058_resort_residency"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")


def _table_exists(bind, name: str) -> bool:
    return name in inspect(bind).get_table_names()


def upgrade():
    bind = op.get_bind()

    if _table_exists(bind, "integrity_events"):
        logger.info("[migration 0059] integrity_events already exists; skipping create_table")
    else:
        op.create_table(
            "integrity_events",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("ts", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("actor", sa.String(64), nullable=False),
            sa.Column("action", sa.String(64), nullable=False),
            sa.Column("scope", sa.String(128), nullable=False),
            sa.Column("ref_id", sa.String(64), nullable=True),
            sa.Column("payload_json", sa.Text, nullable=True),
            sa.Column("prev_hash", sa.String(128), nullable=True),
            sa.Column("event_hash", sa.String(128), nullable=False),
            sa.Column("sig", sa.String(128), nullable=True),
        )

    if _table_exists(bind, "telemetry_events"):
        logger.info("[migration 0059] telemetry_events already exists; skipping create_table")
    else:
        op.create_table(
            "telemetry_events",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("ts", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("category", sa.String(64), nullable=False),
            sa.Column("name", sa.String(128), nullable=False),
            sa.Column("latency_ms", sa.Integer, nullable=True),
            sa.Column("ok", sa.Boolean, nullable=False, server_default=sa.text("true")),
            sa.Column("dim", sa.String(128), nullable=True),
            sa.Column("anomaly", sa.Boolean, nullable=False, server_default=sa.text("false")),
        )

    if _table_exists(bind, "telemetry_counters"):
        logger.info("[migration 0059] telemetry_counters already exists; skipping create_table")
    else:
        op.create_table(
            "telemetry_counters",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("yyyymmdd", sa.String(10), nullable=False),
            sa.Column("category", sa.String(64), nullable=False),
            sa.Column("name", sa.String(128), nullable=False),
            sa.Column("count_ok", sa.Integer, nullable=False, server_default="0"),
            sa.Column("count_err", sa.Integer, nullable=False, server_default="0"),
            sa.Column("p95_ms", sa.Integer, nullable=False, server_default="0"),
        )


def downgrade():
    for t in ["telemetry_counters", "telemetry_events", "integrity_events"]:
        op.drop_table(t)
