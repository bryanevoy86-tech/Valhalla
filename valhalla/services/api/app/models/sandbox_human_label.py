"""Human labels for closed-loop learning."""
from __future__ import annotations

import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.core.db import Base


class HumanLabelValue(str, enum.Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    NEEDS_INFO = "NEEDS_INFO"


class HumanLabel(Base):
    __tablename__ = "human_labels"

    id = Column(Integer, primary_key=True)
    engine_name = Column(String(64), nullable=False, default="wholesaling")
    lead_ref = Column(String(128), nullable=True)       # can be lead_id or external reference
    label = Column(String(16), nullable=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
