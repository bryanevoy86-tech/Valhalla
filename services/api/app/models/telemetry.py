"""
Telemetry models - DEPRECATED.

All telemetry/integrity models have been consolidated into:
- app.integrity.models.IntegrityEvent (maps to telemetry_events table)

This file is kept for backwards compatibility but should not be imported.
"""

# Deprecated: All models moved to app.integrity.models
# Use app.integrity.models.IntegrityEvent instead

# Legacy TelemetryEvent - commented out, use app.integrity.models
# class TelemetryEvent(Base):
#     __tablename__ = "telemetry_events"
#     ...

# Legacy IntegrityEvent - commented out, conflicts with new unified model
# class IntegrityEvent(Base):
#     """Pack 9: Integrity Ledger events"""
#     __tablename__ = "integrity_events"
#     id = Column(Integer, primary_key=True, index=True)
#     ts = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    event = Column(String(200), nullable=False, index=True)
    level = Column(String(16), nullable=False, server_default="info", index=True)
    actor = Column(String(120), nullable=False, server_default="system", index=True)
    meta = Column(Text, nullable=False, server_default="{}")
