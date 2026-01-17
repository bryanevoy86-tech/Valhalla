"""
Pack 49: Global BRRRR Zone Compliance Profiles
ORM models for jurisdictions, compliance_rules, required_documents, tax_bands, compliance_events, risk_flags
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, func
from app.core.db import Base


class Jurisdiction(Base):
    __tablename__ = "jurisdictions"

    id = Column(Integer, primary_key=True, index=True)
    zone_code = Column(String(16), nullable=False, unique=True)
    zone_name = Column(String(128), nullable=False)
    country_code = Column(String(2), nullable=False)
    region = Column(String(64), nullable=True)
    currency = Column(String(3), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id = Column(Integer, primary_key=True, index=True)
    zone_code = Column(String(16), nullable=False, index=True)
    rule_key = Column(String(64), nullable=False)
    rule_value = Column(Text, nullable=False)
    applies_to_deal_types = Column(Text, nullable=True)  # JSON array
    severity = Column(String(16), nullable=False, server_default='warning')
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class RequiredDocument(Base):
    __tablename__ = "required_documents"

    id = Column(Integer, primary_key=True, index=True)
    zone_code = Column(String(16), nullable=False, index=True)
    deal_type = Column(String(32), nullable=False, index=True)
    doc_name = Column(String(128), nullable=False)
    doc_category = Column(String(64), nullable=False)
    is_mandatory = Column(Boolean, nullable=False, server_default="true")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class TaxBand(Base):
    __tablename__ = "tax_bands"

    id = Column(Integer, primary_key=True, index=True)
    zone_code = Column(String(16), nullable=False, index=True)
    tax_type = Column(String(32), nullable=False, index=True)
    min_value = Column(Numeric(14, 2), nullable=False)
    max_value = Column(Numeric(14, 2), nullable=True)
    rate_pct = Column(Numeric(7, 4), nullable=False)
    flat_fee = Column(Numeric(10, 2), nullable=False, server_default="0")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class ComplianceEvent(Base):
    __tablename__ = "compliance_events"

    id = Column(Integer, primary_key=True, index=True)
    zone_code = Column(String(16), nullable=False, index=True)
    deal_type = Column(String(32), nullable=False)
    result = Column(String(16), nullable=False)
    warnings = Column(Text, nullable=True)  # JSON array
    risk_score = Column(Numeric(5, 2), nullable=True)
    snapshot_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())


class RiskFlag(Base):
    __tablename__ = "risk_flags"

    id = Column(Integer, primary_key=True, index=True)
    zone_code = Column(String(16), nullable=False, index=True)
    flag_name = Column(String(64), nullable=False)
    condition = Column(Text, nullable=False)
    risk_impact = Column(String(16), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
