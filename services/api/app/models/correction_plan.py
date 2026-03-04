"""
PACK CL14: Correction Plans
Stores planned fixes/adjustments Heimdall recommends after audits.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from app.models.base import Base


class CorrectionPlan(Base):
    __tablename__ = "correction_plans"

    id = Column(Integer, primary_key=True, index=True)

    plan_id = Column(String, unique=True, index=True, nullable=False)

    # Optional link back to supervision run/finding
    run_id = Column(String, index=True, nullable=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # actions: [{"type":"adjust_weight","path":"leads.score","value":0.2}, ...]
    actions = Column(JSON, nullable=True)

    status = Column(String, nullable=False, default="proposed")  # proposed/approved/applied/rejected

    requires_human_approval = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)
