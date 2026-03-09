"""
Deal Analyzer models for Automated Deal Analysis (Pack 34).
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from app.core.db import Base


class DealAnalysis(Base):
    __tablename__ = "deal_analyses"

    id = Column(Integer, primary_key=True, index=True)
    property_address = Column(String(300), nullable=False, index=True)
    purchase_price = Column(Float, nullable=False)
    rehab_cost = Column(Float, nullable=False)
    arv = Column(Float, nullable=False)  # After Repair Value
    expected_profit = Column(Float, nullable=False)
    roi = Column(Float, nullable=False)  # Return on Investment (percentage)
    cash_on_cash_return = Column(Float, nullable=True)  # Cash-on-cash return percentage
    is_profitable = Column(Boolean, default=True, nullable=False)
    risk_score = Column(Float, nullable=True)  # 0-100, higher = riskier
    ai_recommendation = Column(String(50), default="review")  # pass, review, reject
    analysis_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<DealAnalysis(address={self.property_address}, roi={self.roi}%, profitable={self.is_profitable})>"
