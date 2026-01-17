from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from app.models.base import Base


class RiskEvent(Base):
    """
    Every risk decision is logged:
    - reserve approved
    - reserve denied (hard stop)
    - settle (release reserve, apply loss)
    """
    __tablename__ = "risk_event"

    id = Column(Integer, primary_key=True, index=True)

    engine = Column(String, nullable=False)
    action = Column(String, nullable=False)  # "RESERVE", "DENY", "SETTLE", "RELEASE"
    amount = Column(Float, nullable=False, default=0.0)  # exposure/reserve/loss amount

    ok = Column(Boolean, nullable=False, default=True)
    reason = Column(String, nullable=True)

    # Traceability
    correlation_id = Column(String, nullable=True)
    actor = Column(String, nullable=True)  # human/system identifier
    metadata_json = Column(Text, nullable=True)  # store JSON string if desired

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
