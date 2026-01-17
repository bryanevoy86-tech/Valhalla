from pydantic import BaseModel, ConfigDict
from typing import Optional


class GateSnapshot(BaseModel):
    uptime_pct: float
    cash_reserves: float
    net_margin_pct: float
    audit_score: float
    error_rate_ppm: int
    traffic_p90_rps: Optional[float] = None
    latency_p95_ms: Optional[float] = None


class ClonePolicyIn(BaseModel):
    enabled: bool
    min_days_between: int
    max_active: int
    required_uptime_pct: float
    required_cash_reserves: float
    required_net_margin_pct: float
    required_audit_score: float
    max_error_rate_ppm: int


class ClonePolicyOut(ClonePolicyIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    last_triggered_at: Optional[str] = None


class MirrorPolicyIn(BaseModel):
    enabled: bool
    min_days_between: int
    max_active: int
    required_p90_rps: float
    required_p95_latency_ms: float


class MirrorPolicyOut(MirrorPolicyIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    last_triggered_at: Optional[str] = None


class EvaluateResult(BaseModel):
    allow: bool
    reason: str
