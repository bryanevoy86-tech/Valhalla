from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.db import Base


class TaxOpinion(Base):
    __tablename__ = "tax_opinions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # e.g. "CA-CRA", "US-IRS", "PA-Panama", etc.
    jurisdiction = Column(String(20), nullable=False)
    tax_year = Column(String(10), nullable=True)  # "2025", "2025/2026", etc.

    # who produced the opinion
    source = Column(String(30), nullable=False)  # "accountant" | "ai" | "lawyer"
    specialist_id = Column(UUID(as_uuid=True), nullable=True)  # link to HumanSpecialist

    case_id = Column(UUID(as_uuid=True), nullable=True)  # link into dual-god case if needed

    summary = Column(Text, nullable=True)
    details = Column(JSONB, nullable=True)  # structured explanation

    # "safe", "moderate", "aggressive", etc.
    risk_level = Column(String(20), nullable=True)
    flags = Column(JSONB, nullable=True)  # e.g. {"cra_audit_risk": "low", "documentation_needed": [...]}