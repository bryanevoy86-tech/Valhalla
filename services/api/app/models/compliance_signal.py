from sqlalchemy import Column, Integer, String, DateTime, Float
from app.db.base_class import Base
import datetime

class ComplianceSignal(Base):
    __tablename__ = "compliance_signals"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, nullable=True)
    source = Column(String, nullable=False)
    severity = Column(String, default="info")
    code = Column(String)
    message = Column(String)
    score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
