from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from app.models.base import Base


class HeimdallRecommendation(Base):
    """
    A single recommendation with an evidence trace.
    Must be attributable, replayable, and auditable.
    """
    __tablename__ = "heimdall_recommendation"

    id = Column(Integer, primary_key=True, index=True)

    domain = Column(String, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)

    # Recommendation payload and evidence payload are stored as JSON string
    recommendation_json = Column(Text, nullable=False)
    evidence_json = Column(Text, nullable=True)

    # Linkage / traceability
    correlation_id = Column(String, nullable=True)
    actor = Column(String, nullable=True)  # who requested / applied it

    # Governance results
    prod_eligible = Column(Boolean, nullable=False, default=False)
    gate_reason = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
