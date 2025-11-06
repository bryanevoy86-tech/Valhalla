"""
Negotiation Technique models for Pack 32.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.core.db import Base


class NegotiationTechnique(Base):
    __tablename__ = "negotiation_techniques_advanced"

    id = Column(Integer, primary_key=True, index=True)
    technique_name = Column(String(200), nullable=False, index=True)
    description = Column(String(1000), nullable=False)
    effectiveness_score = Column(Float, nullable=False)  # 0-100 scale
    technique_type = Column(String(100), nullable=True)  # e.g., Anchoring, Framing, Persuasion
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<NegotiationTechnique(name={self.technique_name}, score={self.effectiveness_score})>"
