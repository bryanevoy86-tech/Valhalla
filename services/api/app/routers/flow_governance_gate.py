# services/api/app/routers/flow_governance_gate.py

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.models.audit_log import AuditLog
from app.routers.flow_full_pipeline import build_full_deal_pipeline
from app.routers.governance_orchestrator import evaluate_all
from app.schemas.flow_full_pipeline import FullDealPipelineRequest
from app.schemas.governance import GovernanceEvaluationRequest

router = APIRouter(
    prefix="/flow",
    tags=["Flow", "Governance"],
    dependencies=[Depends(require_prime_control_key)],
)


class GovernedDealRequest(FullDealPipelineRequest):
    governance: dict[str, Any] = Field(default_factory=dict)


@router.post(
    "/full_deal_with_governance",
    status_code=status.HTTP_201_CREATED,
    summary="Full deal pipeline gated by governance",
    description=(
        "Runs /governance/evaluate_all first. If the pantheon approves, "
        "executes /flow/full_deal_pipeline. Otherwise returns 409 with "
        "governance details and does NOT create/modify any deals."
    ),
)
def full_deal_with_governance(payload: GovernedDealRequest, db: Session = Depends(get_db)):
    """Run all five advisory specialists before writing internal deal records."""
    governance_flags = payload.governance
    price = payload.underwriting.purchase_price
    repairs = payload.underwriting.repairs
    arv = payload.underwriting.arv
    roi = (arv - price - repairs) / price if price > 0 else Decimal("0")

    # Build shared governance data
    gov_data: Dict[str, Any] = {
        # King-ish
        "purchase_price": str(price),
        "repairs": str(repairs),
        "arv": str(arv),
        "roi": str(roi),
        "predatory": str(governance_flags.get("predatory", False)),
        # Queen-ish (use safe defaults; you can override via payload['governance'])
        "hours_per_week": str(governance_flags.get("hours_per_week", 40)),
        "parallel_projects": str(governance_flags.get("parallel_projects", 1)),
        "uses_evenings": str(governance_flags.get("uses_evenings", False)),
        "uses_weekends": str(governance_flags.get("uses_weekends", False)),
        "sprint_weeks": str(governance_flags.get("sprint_weeks", 4)),
        "stress_level": str(governance_flags.get("stress_level", 6)),
        "chaos_factor": str(governance_flags.get("chaos_factor", 4.0)),
        # Odin-ish
        "active_verticals": str(governance_flags.get("active_verticals", 1)),
        "new_verticals": str(governance_flags.get("new_verticals", 0)),
        "estimated_annual_profit": str(governance_flags.get("estimated_annual_profit", 150000)),
        "complexity_score": str(governance_flags.get("complexity_score", 5)),
        "time_to_break_even_months": str(governance_flags.get("time_to_break_even_months", 12)),
        "mission_critical": str(governance_flags.get("mission_critical", True)),
        "distraction_score": str(governance_flags.get("distraction_score", 2)),
        # Loki-ish
        "capital_at_risk": str(governance_flags.get("capital_at_risk", price)),
        "worst_case_loss": str(governance_flags.get("worst_case_loss", price)),
        "probability_of_ruin": str(governance_flags.get("probability_of_ruin", 0.02)),
        "correlation_with_portfolio": str(governance_flags.get("correlation_with_portfolio", 0.5)),
        "hidden_complexity_score": str(governance_flags.get("hidden_complexity_score", 5)),
        # Tyr-ish
        "requires_license_without_having_it": str(
            governance_flags.get("requires_license_without_having_it", False)
        ),
        "tax_evasion": str(governance_flags.get("tax_evasion", False)),
        "fraudulent_misrepresentation": str(governance_flags.get("fraudulent_misrepresentation", False)),
        "recording_without_consent": str(governance_flags.get("recording_without_consent", False)),
        "exploits_vulnerable": str(governance_flags.get("exploits_vulnerable", False)),
        "misleading_marketing": str(governance_flags.get("misleading_marketing", False)),
        "missing_disclosures": str(governance_flags.get("missing_disclosures", False)),
    }

    decision = evaluate_all(GovernanceEvaluationRequest(context_type="deal", data=gov_data))
    if not decision.overall_allowed or not decision.full_coverage:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Governance blocked internal deal intake.",
                "governance": decision.model_dump(mode="json"),
            },
        )
    pipeline = build_full_deal_pipeline(payload, db)
    db.add(AuditLog(
        deal_id=pipeline.backend_deal_id,
        event_type="internal_deal_governance",
        event_source="system",
        message="Five-specialist evaluation recorded for internal intake",
        event_data=decision.model_dump_json(),
    ))
    db.commit()
    return {**pipeline.model_dump(mode="json"), "_governance": decision.model_dump(mode="json")}
