from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import datetime

class UnderwriterAssessment(Base):
    __tablename__ = "underwriter_assessments"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, nullable=False)  # FK logical link to deals

    risk_score = Column(Float, default=0.0)          # 0–100
    legal_risk_score = Column(Float, default=0.0)    # 0–100
    profitability_score = Column(Float, default=0.0) # 0–100

    decision = Column(String, default="review")     # approve / reject / review
    notes = Column(String)

    country = Column(String)
    region = Column(String)
    legal_profile_id = Column(Integer, ForeignKey("legal_profiles.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    legal_profile = relationship("LegalProfile", lazy="joined")
