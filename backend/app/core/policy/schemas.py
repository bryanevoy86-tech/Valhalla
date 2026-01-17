from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Dict, Optional, Literal

AutonomyLevel = Literal["L0", "L1", "L2", "L3", "L4"]


class PolicySafety(BaseModel):
    max_risk_per_action_pct: float
    max_exposure_per_leg_pct: float
    max_weekly_drawdown_pct: float
    max_monthly_drawdown_pct: float
    correlated_risk_cap_pct: float
    default_cash_buffer_pct: float
    crisis_cash_buffer_pct: float


class PolicyAutonomy(BaseModel):
    l1_recommend_min_samples: int
    l2_auto_execute_min_samples: int
    l3_auto_scale_min_samples: int
    l4_auto_prune_min_samples: int
    l2_max_variance_pct: float
    l3_max_variance_pct: float
    l4_max_variance_pct: float


class PolicyOptimization(BaseModel):
    min_ev: float
    min_confidence_pct: float
    max_downside_to_ev_ratio: float
    score_weights: Dict[str, float]
    time_to_cash_months_soft_cap: int


class PolicyPortfolio(BaseModel):
    exploration_floor_pct: float


class UnifiedPolicy(BaseModel):
    version: str
    name: str
    safety: PolicySafety
    autonomy: PolicyAutonomy
    optimization: PolicyOptimization
    portfolio: PolicyPortfolio


class DecisionCandidate(BaseModel):
    leg: str = Field(..., description="Which revenue leg/module this belongs to")
    ev: float = Field(..., description="Expected value (normalized)")
    downside: float = Field(..., description="Downside magnitude (normalized)")
    confidence_pct: float = Field(..., ge=0, le=100)
    time_to_cash_months: int = Field(..., ge=0)
    strategic_value: float = 0.0

    proposed_risk_pct_of_capital: float = Field(..., ge=0)
    proposed_exposure_pct_of_leg: float = Field(..., ge=0)

    estimated_variance_pct: Optional[float] = None
    autonomy_level: AutonomyLevel = "L1"
