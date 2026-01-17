# services/api/app/schemas/governance.py

from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# -----------------------------------------------
# KING POLICY CONFIGURATION
# -----------------------------------------------

class KingRiskTolerance(BaseModel):
    """
    Defines high-level risk thresholds that apply to ALL businesses
    Valhalla operates, not just real estate.
    """

    max_allowed_investment: Decimal = Field(
        default=Decimal("500000"),
        description="Maximum spend allowed without King override."
    )

    min_expected_roi: Decimal = Field(
        default=Decimal("0.12"),
        description="Minimum ROI required for King to allow execution (12%)."
    )

    max_repair_risk_factor: Decimal = Field(
        default=Decimal("0.30"),
        description="If repairs exceed 30% of purchase, flag as high risk."
    )

    allow_high_leverage: bool = Field(
        default=False,
        description="If False, projects requiring >80% leverage require override."
    )


class KingMission(BaseModel):
    """
    Defines the long-term mission objectives.
    This is NOT business-specific — it's Valhalla-wide strategy.
    """

    prioritize_cashflow: bool = True
    prioritize_equity_growth: bool = True
    prioritize_passive_income: bool = False
    prioritize_speed: bool = True


class KingValues(BaseModel):
    """
    The values the King enforces.
    Everything Heimdall builds must respect these.
    """

    transparency: bool = True
    sustainability: bool = True
    minimal_risk: bool = True
    ethical_acquisition: bool = True
    avoid_predatory_tactics: bool = True


class KingPolicy(BaseModel):
    """
    Full King policy specification.
    Loaded during system startup.
    """

    risk: KingRiskTolerance = KingRiskTolerance()
    mission: KingMission = KingMission()
    values: KingValues = KingValues()


# -----------------------------------------------
# KING EVALUATION REQUEST / RESPONSE
# -----------------------------------------------

class KingEvaluationContext(BaseModel):
    """
    What the King receives to evaluate any deal, project, or build request.
    """

    context_type: str = Field(
        ...,
        description="e.g., 'deal', 'profit_event', 'build_request', 'feature_expansion'"
    )
    data: Dict[str, str] = Field(
        default_factory=dict,
        description="A dictionary of key details (price, arv, roi, industry, etc.)"
    )


class KingDecision(BaseModel):
    """
    Result of King evaluating a request.
    """

    allowed: bool
    severity: str  # info, warn, critical
    reasons: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


# -----------------------------------------------
# QUEEN POLICY CONFIGURATION
# -----------------------------------------------

class QueenEnergy(BaseModel):
    """
    How much personal energy and time the Queen is willing to spend.
    This is about YOU and your family, not just the business.
    """

    max_hours_per_week: int = Field(
        default=40,
        description="Preferred maximum hours per week you want to work in the system.",
    )
    hard_cap_hours_per_week: int = Field(
        default=55,
        description="Absolute upper limit before Queen orders a hard stop / freeze.",
    )
    max_parallel_projects: int = Field(
        default=3,
        description="How many major projects can be active at once without overload.",
    )


class QueenFamily(BaseModel):
    """
    Guardrails around family impact.
    """

    protect_evenings: bool = Field(
        default=True,
        description="If True, Queen will flag work that consumes most evenings.",
    )
    protect_weekends: bool = Field(
        default=True,
        description="If True, Queen will flag work that eats weekends.",
    )
    allow_short_sprints: bool = Field(
        default=True,
        description="If True, occasional intense sprints are allowed if limited in time.",
    )


class QueenStress(BaseModel):
    """
    How the Queen reacts to stress, chaos, and emotional load.
    """

    max_stress_level: int = Field(
        default=7,
        description="1-10 scale: above this, Queen starts flagging overload.",
    )
    hard_cap_stress_level: int = Field(
        default=9,
        description="1-10 scale: above this, Queen can force a pause/freeze.",
    )


class QueenPolicy(BaseModel):
    """
    Full Queen policy specification.
    """

    energy: QueenEnergy = QueenEnergy()
    family: QueenFamily = QueenFamily()
    stress: QueenStress = QueenStress()


# -----------------------------------------------
# ODIN STRATEGY POLICY CONFIGURATION
# -----------------------------------------------

class OdinStrategy(BaseModel):
    """
    High-level strategic constraints for new business lines, projects, and
    major experiments. This is about 'Should we do this at all?'
    """

    max_active_verticals: int = Field(
        default=5,
        description="How many major business verticals Valhalla can run at once."
    )
    min_estimated_annual_profit: Decimal = Field(
        default=Decimal("100000"),
        description="Minimum estimated annual profit for a new vertical to be worth it."
    )
    max_complexity_score: int = Field(
        default=7,
        description="1-10 scale: above this, the project is considered too complex right now."
    )
    max_time_to_break_even_months: int = Field(
        default=18,
        description="If break-even > this, Odin will likely reject or warn."
    )


class OdinPolicy(BaseModel):
    """
    Full Odin policy specification.
    Odin looks at strategic fit and ROI of *big* decisions.
    """

    strategy: OdinStrategy = OdinStrategy()


# -----------------------------------------------
# LOKI RISK INVERSION POLICY CONFIGURATION
# -----------------------------------------------

class LokiRiskProfile(BaseModel):
    """
    Loki looks at the *downside*:
    - How bad can this go?
    - How likely is ruin?
    - How entangled is this with everything else?
    """

    max_downside_multiplier: Decimal = Field(
        default=Decimal("1.5"),
        description=(
            "Maximum acceptable downside relative to capital at risk. "
            "Example: 1.5 means worst-case loss of 150% of capital is too much."
        ),
    )
    max_probability_of_ruin: Decimal = Field(
        default=Decimal("0.05"),
        description="Maximum acceptable probability of ruin (0.05 = 5%).",
    )
    max_correlation_with_portfolio: Decimal = Field(
        default=Decimal("0.80"),
        description="If correlation with existing risk > 0.8, Loki flags it.",
    )
    max_hidden_complexity_score: int = Field(
        default=7,
        description="1-10 scale: above this, hidden complexity is too high.",
    )


class LokiPolicy(BaseModel):
    """
    Full Loki policy specification.
    """

    risk: LokiRiskProfile = LokiRiskProfile()


# -----------------------------------------------
# TYR LEGAL & ETHICAL POLICY CONFIGURATION
# -----------------------------------------------

class TyrLegalPolicy(BaseModel):
    """
    Tyr guards legal and contractual red lines.
    """

    forbid_unlicensed_practice: bool = Field(
        default=True,
        description="If True, flags actions that require a license the system/user doesn't have.",
    )
    forbid_tax_evasion: bool = Field(
        default=True,
        description="If True, flags any attempt to hide income or fabricate expenses.",
    )
    forbid_fraudulent_misrepresentation: bool = Field(
        default=True,
        description="If True, flags lying about material facts in deals or offers.",
    )
    require_written_consent_for_recording: bool = Field(
        default=True,
        description="If True, flags recording calls without proper consent where required.",
    )


class TyrEthicsPolicy(BaseModel):
    """
    Tyr guards core ethical standards for Valhalla.
    """

    forbid_exploiting_vulnerable: bool = Field(
        default=True,
        description="If True, forbids deals that explicitly prey on vulnerable people.",
    )
    forbid_misleading_marketing: bool = Field(
        default=True,
        description="If True, forbids deceptive claims in advertising.",
    )
    require_clear_disclosures: bool = Field(
        default=True,
        description="If True, flags missing disclosures on risk, terms, or conflicts.",
    )


class TyrPolicy(BaseModel):
    """
    Full Tyr policy specification.
    """

    legal: TyrLegalPolicy = TyrLegalPolicy()
    ethics: TyrEthicsPolicy = TyrEthicsPolicy()


# -----------------------------------------------
# AGGREGATED GOVERNANCE EVALUATION
# -----------------------------------------------

class GovernanceCheckResult(BaseModel):
    """
    Result of a single god's evaluation (King, Queen, Odin, Loki, Tyr).
    """

    god: Literal["king", "queen", "odin", "loki", "tyr"]
    allowed: bool
    severity: str  # info, warn, critical
    reasons: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class GovernanceAggregateDecision(BaseModel):
    """
    Combined decision across multiple gods.
    """

    overall_allowed: bool
    worst_severity: str  # info, warn, critical
    blocked_by: List[str] = Field(
        default_factory=list,
        description="List of gods that issued a critical denial.",
    )
    checks: List[GovernanceCheckResult] = Field(
        default_factory=list,
        description="Per-god detailed decisions.",
    )
    summary: Optional[str] = None


class GovernanceEvaluationRequest(BaseModel):
    """
    Request for multi-god evaluation via /governance/evaluate_all.
    """

    context_type: str = Field(
        ...,
        description="e.g. 'deal', 'new_vertical', 'build_request'",
    )
    data: Dict[str, str] = Field(
        default_factory=dict,
        description="Key-value context for all gods (price, roi, hours_per_week, etc.).",
    )
    gods: Optional[List[Literal["king", "queen", "odin", "loki", "tyr"]]] = Field(
        default=None,
        description="If set, restrict evaluation to these gods; otherwise, evaluate all.",
    )


# -----------------------------------------------
# GOVERNANCE POLICY AGGREGATE VIEW
# -----------------------------------------------

class GovernancePolicies(BaseModel):
    """
    Snapshot of all governance policies currently loaded in-memory.
    This is what the policy API returns so the UI / tools can see
    how the Gods are configured.
    """

    king: KingPolicy
    queen: QueenPolicy
    odin: OdinPolicy
    loki: LokiPolicy
    tyr: TyrPolicy
