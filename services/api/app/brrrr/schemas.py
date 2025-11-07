"""
Pack 49: Global BRRRR Zone Compliance Profiles
Pydantic schemas for zone evaluation, checklist, and tax calculation
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


class ZoneOut(BaseModel):
    """Jurisdiction output"""
    id: int
    zone_code: str
    zone_name: str
    country_code: str
    region: Optional[str] = None
    currency: str
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ChecklistItem(BaseModel):
    """Required document checklist item"""
    doc_name: str
    doc_category: str
    is_mandatory: bool
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class EvaluateIn(BaseModel):
    """Input for compliance evaluation"""
    zone: str
    deal_type: str
    purchase_price: Decimal
    arv: Decimal
    ltv: Optional[float] = None
    entity_type: Optional[str] = None
    foreign_owner: bool = False


class TaxEstimate(BaseModel):
    """Tax calculation result"""
    tax_type: str
    base_value: Decimal
    rate_pct: float
    flat_fee: Decimal
    total: Decimal


class EvaluateOut(BaseModel):
    """Compliance evaluation result"""
    ok: bool
    warnings: List[str]
    risk_score: float
    checklist: List[ChecklistItem]
    taxes: List[TaxEstimate]
    notes: Optional[str] = None


class RuleOut(BaseModel):
    """Compliance rule output"""
    id: int
    zone_code: str
    rule_key: str
    rule_value: str
    applies_to_deal_types: Optional[str] = None
    severity: str
    model_config = ConfigDict(from_attributes=True)


class FlagOut(BaseModel):
    """Risk flag output"""
    id: int
    zone_code: str
    flag_name: str
    condition: str
    risk_impact: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
