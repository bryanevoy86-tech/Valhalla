from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, UniqueConstraint
from app.models.base import Base


class MarketPolicy(Base):
    """
    Province/market governance. This is how you go Canada-wide without chaos.
    Stores JSON string rules per province + optional market subtag.
    """
    __tablename__ = "market_policy"
    __table_args__ = (UniqueConstraint("province", "market", name="uq_market_policy_province_market"),)

    id = Column(Integer, primary_key=True, index=True)

    # Province: BC, AB, SK, MB, ON, QC, NB, NS, PE, NL, YT, NT, NU
    province = Column(String, nullable=False)
    # Optional market label inside province (e.g., "TORONTO", "WINNIPEG")
    market = Column(String, nullable=False, default="ALL")

    enabled = Column(Boolean, nullable=False, default=True)

    # JSON string:
    # {
    #   "contact_windows_local": [{"days":[0,1,2,3,4], "start":"09:00", "end":"20:00"}],
    #   "channels_allowed": ["SMS","CALL","EMAIL"],
    #   "min_lead_score_to_contact": 0.65
    # }
    rules_json = Column(Text, nullable=False)

    changed_by = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
