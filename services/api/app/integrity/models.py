"""Pack 59: Integrity + Telemetry - Models"""
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.db import Base

# REMOVE OR COMMENT OUT — Pack 59 duplicate
# Use the canonical IntegrityEvent from app.models.telemetry instead
# class IntegrityEvent(Base):
#     __tablename__ = "integrity_events"
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     ts: Mapped[str] = mapped_column(DateTime, server_default=func.now())
#     actor: Mapped[str] = mapped_column(String(64), nullable=False)
#     action: Mapped[str] = mapped_column(String(64), nullable=False)
#     scope: Mapped[str] = mapped_column(String(128), nullable=False)
#     ref_id: Mapped[str | None] = mapped_column(String(64))
#     payload_json: Mapped[str | None] = mapped_column(Text)
#     prev_hash: Mapped[str | None] = mapped_column(String(128))
#     event_hash: Mapped[str] = mapped_column(String(128), nullable=False)
#     sig: Mapped[str | None] = mapped_column(String(128))

class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts: Mapped[str] = mapped_column(DateTime, server_default=func.now())
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    dim: Mapped[str | None] = mapped_column(String(128))
    anomaly: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

class TelemetryCounter(Base):
    __tablename__ = "telemetry_counters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    yyyymmdd: Mapped[str] = mapped_column(String(10), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    count_ok: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    count_err: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    p95_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
