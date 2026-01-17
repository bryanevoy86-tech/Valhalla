"""PACK 95: Expansion Risk & Compliance - Models"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.models.base import Base


class ExpansionRiskRule(Base):
    __tablename__ = "expansion_risk_rule"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, nullable=False)
    rule_name = Column(String, nullable=False)
    risk_payload = Column(Text, nullable=False)     # JSON: tax rules, legal flags, market volatility
    created_at = Column(DateTime, default=datetime.utcnow)


class ExpansionComplianceCheck(Base):
    __tablename__ = "expansion_compliance_check"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, nullable=False)
    status = Column(String, default="pending")     # pending, passed, failed
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
