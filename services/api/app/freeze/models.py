from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text, JSON, func
from datetime import datetime, timezone
from typing import Any, Optional
from app.core.db import Base


class FreezeRule(Base):
    __tablename__ = "freeze_rules"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # e.g., "drawdown_guard"
    metric = Column(String, nullable=False)  # e.g., "fx_drawdown_pct"
    threshold = Column(Float, nullable=False)  # e.g., 2.0
    comparator = Column(String, default=">")  # ">", "<", ">=", "<="
    active = Column(Boolean, default=True)
    scope = Column(String, nullable=True)  # "arbitrage", "all"


class FreezeEvent(Base):
    """
    ORM model for freeze_events matching Alembic migration 126.
    
    Updated schema includes:
    - id, created_at, source, event_type, reason, severity
    - payload (JSON), resolved_at, resolved_by, notes
    """
    __tablename__ = "freeze_events"
    id = Column(Integer, primary_key=True, index=True, nullable=False)
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    
    source = Column(
        String(length=100),
        nullable=True,
        comment="What triggered the freeze (scheduler job, policy, manual, etc.)",
    )
    
    event_type = Column(
        String(length=50),
        nullable=True,
        index=True,
        comment="Short code for the freeze reason (e.g. 'liquidity', 'policy_violation').",
    )
    
    reason = Column(
        Text,
        nullable=True,
        comment="Human-readable reason for the freeze.",
    )
    
    severity = Column(
        String(length=20),
        nullable=True,
        index=True,
        comment="Optional severity level (info/warn/critical).",
    )
    
    payload = Column(
        JSON,
        nullable=True,
        comment="Optional structured data captured at freeze time.",
    )
    
    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When (if) this freeze event was fully resolved.",
    )
    
    resolved_by = Column(
        String(length=100),
        nullable=True,
        comment="Who or what resolved the freeze (user, job, Heimdall).",
    )
    
    notes = Column(
        Text,
        nullable=True,
        comment="Free-form notes for extra context.",
    )

    def to_safe_payload(self) -> Optional[dict[str, Any]]:
        """
        Convenience helper to ensure payload is always a dict for the API.
        """
        if self.payload is None:
            return None
        if isinstance(self.payload, dict):
            return self.payload
        return {"raw": self.payload}
