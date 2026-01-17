from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone
from app.core.db import Base


class ComplianceRecord(Base):
    __tablename__ = "compliance_records"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # e.g., "Vehicle", "Home Office"
    claimed_amount = Column(Float, nullable=False)
    risk_score = Column(Float, default=0.0)  # 0–100 scale
    rating = Column(String, default="Safe")  # Safe / Moderate / Aggressive
    justification = Column(String, nullable=True)
    date_logged = Column(DateTime, default=lambda: datetime.now(timezone.utc))
