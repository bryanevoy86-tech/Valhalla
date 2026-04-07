# services/api/app/routers/flow_governance_gate.py

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.testclient import TestClient

router = APIRouter(
    prefix="/flow",
    tags=["Flow", "Governance"],
)


def _get_client():
    """Get a fresh TestClient for the app. Import here to avoid circular imports."""
    from app.main import app
    return TestClient(app)


def _dec(val: Any) -> Optional[Decimal]:
    if val is None:
        return None
    try:
        return Decimal(str(val))
    except Exception:
        return None


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
def full_deal_with_governance(payload: Dict[str, Any]):
    """
    Wraps the existing full_deal_pipeline endpoint with the governance layer.

    Expected payload:
    - Same fields as /flow/full_deal_pipeline (lead, deal, match_settings, underwriting, ...)
    - Optional 'governance' key for extra flags (e.g., tax_evasion=True, exploits_vulnerable=True).
    """
    client = _get_client()
    
    deal = payload.get("deal", {}) or {}
    underwriting = payload.get("underwriting", {}) or {}
    governance_flags = payload.get("governance", {}) or {}

    # Extract core financials
    price = underwriting.get("purchase_price") or deal.get("price")
    repairs = underwriting.get("repairs") or deal.get("repairs")
    arv = underwriting.get("arv") or deal.get("arv")

    price_dec = _dec(price)
    repairs_dec = _dec(repairs) or Decimal("0")
    arv_dec = _dec(arv)

    roi_dec: Optional[Decimal] = None
    if price_dec and arv_dec:
        try:
            roi_dec = (arv_dec - price_dec - repairs_dec) / price_dec
        except Exception:
            roi_dec = None

    # Build shared governance data
    gov_data: Dict[str, Any] = {
        # King-ish
        "purchase_price": str(price_dec) if price_dec is not None else "0",
        "repairs": str(repairs_dec) if repairs_dec is not None else "0",
        "arv": str(arv_dec) if arv_dec is not None else "0",
        "roi": str(roi_dec) if roi_dec is not None else "0",
        "predatory": "False",
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

    # Merge/override with explicit governance flags if provided, converting all to strings
    for key, val in governance_flags.items():
        if key not in gov_data:
            gov_data[key] = str(val)
        else:
            gov_data[key] = str(val)

    # 1) Call governance orchestrator
    gov_body = {
        "context_type": "deal",
        "data": gov_data,
        "gods": None,  # evaluate all by default
    }

    gov_resp = client.post("/api/governance/evaluate_all", json=gov_body)
    if gov_resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"governance/evaluate_all failed: {gov_resp.status_code} {gov_resp.text}",
        )

    governance_decision = gov_resp.json()

    if not governance_decision.get("overall_allowed", False):
        # Governance blocked the plan – do not call full_deal_pipeline
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Governance blocked this deal pipeline execution.",
                "governance": governance_decision,
            },
        )

    # 2) Governance OK – call the real pipeline
    pipeline_resp = client.post("/api/flow/full_deal_pipeline", json=payload)
    if pipeline_resp.status_code not in (200, 201):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"full_deal_pipeline failed: {pipeline_resp.status_code} {pipeline_resp.text}",
        )

    pipeline_data = pipeline_resp.json()
    # Attach governance snapshot for traceability
    pipeline_data["_governance"] = governance_decision
    return pipeline_data
