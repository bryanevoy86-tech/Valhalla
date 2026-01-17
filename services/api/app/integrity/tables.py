"""Core SQLAlchemy Table definitions for Integrity/Telemetry.

Provides a safe Table handle for `telemetry_events` that:
- Reuses the existing table from Base.metadata if already defined by ORM
- Otherwise defines the table with columns matching migration 0059
- Uses extend_existing=True to avoid MetaData collisions
"""
from sqlalchemy import Table, Column, Integer, String, Text, DateTime, Boolean, text
from app.core.db import Base


def get_telemetry_events_table() -> Table:
    existing = Base.metadata.tables.get("telemetry_events")
    if existing is not None:
        return existing
    return Table(
        "telemetry_events",
        Base.metadata,
        Column("id", Integer, primary_key=True),
        Column("ts", DateTime, server_default=text("CURRENT_TIMESTAMP")),
        Column("category", String(64), nullable=False),
        Column("name", String(128), nullable=False),
        Column("latency_ms", Integer),
        Column("ok", Boolean, nullable=False, server_default=text("true")),
        Column("dim", String(128)),
        Column("anomaly", Boolean, nullable=False, server_default=text("false")),
        extend_existing=True,
    )


telemetry_events: Table = get_telemetry_events_table()

__all__ = ["telemetry_events", "get_telemetry_events_table"]
