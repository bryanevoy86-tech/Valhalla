from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from app.db.base_class import Base
import datetime


class GovernanceSettings(Base):
    __tablename__ = "governance_settings"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False, unique=True)    # "primary_governance"

    # overall mode: "manual", "hybrid", "full_auto"
    mode = Column(String, default="hybrid")

    # hard caps (in CAD-equivalent)
    max_auto_transfer = Column(Float, default=1000.0)
    max_auto_contract_commit = Column(Float, default=5000.0)

    # require Bryan approval for these
    require_approval_new_zone = Column(Boolean, default=True)
    require_approval_new_legacy = Column(Boolean, default=True)
    require_approval_large_hire = Column(Boolean, default=True)

    # safety toggles
    shield_always_on = Column(Boolean, default=True)
    log_all_decisions = Column(Boolean, default=True)

    notes = Column(Text)

    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
