from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class EmpireHealthSummary(BaseModel):
    service_name: str
    status: str
    issue_count: int
    last_heartbeat: Optional[datetime]


class EmpireShieldSummary(BaseModel):
    total_events: int
    pending_events: int
    high_severity_events: int


class EmpireLegalSummary(BaseModel):
    total_profiles: int
    active_profiles: int
    high_risk_profiles: int


class EmpireLegacySummary(BaseModel):
    total_legacies: int
    active_legacies: int
    auto_clone_enabled: int


class EmpireTrustSummary(BaseModel):
    total_trusts: int
    active_trusts: int
    total_vault_balance: float


class EmpireComplianceSummary(BaseModel):
    total_signals: int
    warnings: int
    critical: int


class EmpireStatusOut(BaseModel):
    health: List[EmpireHealthSummary]
    shield: EmpireShieldSummary
    trusts: EmpireTrustSummary
    legacies: EmpireLegacySummary
    legal: EmpireLegalSummary
    compliance: EmpireComplianceSummary

    class Config:
        orm_mode = True
