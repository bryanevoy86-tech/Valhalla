from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Index
from app.models.base import Base


class KPIEvent(Base):
    """
    Business KPI events (not infra metrics).
    Examples:
      - domain="WHOLESALE", metric="offer_accept_rate", success=True
      - domain="BUYER_MATCH", metric="match_success", success=True
      - domain="CAPITAL", metric="roi_event", value=1234.56
    """
    __tablename__ = "kpi_event"

    id = Column(Integer, primary_key=True, index=True)

    domain = Column(String, nullable=False)     # e.g. WHOLESALE, BUYER_MATCH, CAPITAL, FOLLOWUPS
    metric = Column(String, nullable=False)     # e.g. contract_rate, response_rate, profit_event
    success = Column(Boolean, nullable=True)    # for binary outcomes
    value = Column(Float, nullable=True)        # for numeric outcomes (profit, roi, etc.)

    actor = Column(String, nullable=True)
    correlation_id = Column(String, nullable=True)
    detail = Column(Text, nullable=True)        # optional JSON string

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


Index("ix_kpi_domain_metric_time", KPIEvent.domain, KPIEvent.metric, KPIEvent.created_at)
