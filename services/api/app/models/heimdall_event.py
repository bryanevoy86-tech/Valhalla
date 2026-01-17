from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from app.models.base import Base


class HeimdallEvent(Base):
    """
    Audit trail:
    - RECOMMEND_CREATED
    - PROD_GATE_PASS / PROD_GATE_FAIL
    - REGRESSION_BLOCK
    - OVERRIDE_APPLIED (if you ever choose to allow it)
    """
    __tablename__ = "heimdall_event"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, nullable=False)
    event = Column(String, nullable=False)

    ok = Column(Boolean, nullable=False, default=True)
    confidence = Column(Float, nullable=True)

    recommendation_id = Column(Integer, nullable=True)
    correlation_id = Column(String, nullable=True)
    actor = Column(String, nullable=True)

    detail = Column(Text, nullable=True)  # JSON string or plain text
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
