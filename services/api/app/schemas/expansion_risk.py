"""PACK 95: Expansion Risk & Compliance - Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ExpansionRiskRuleBase(BaseModel):
    zone_id: int
    rule_name: str
    risk_payload: str


class ExpansionRiskRuleCreate(ExpansionRiskRuleBase):
    pass


class ExpansionRiskRuleOut(ExpansionRiskRuleBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExpansionComplianceBase(BaseModel):
    zone_id: int
    status: str = "pending"
    notes: str | None = None


class ExpansionComplianceCreate(ExpansionComplianceBase):
    pass


class ExpansionComplianceOut(ExpansionComplianceBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
