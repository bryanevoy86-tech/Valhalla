from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.testclient import TestClient


from app.schemas.heimdall_build import HeimdallBuildRequest, HeimdallBuildResponse

router = APIRouter(
    prefix="/governance",
    tags=["Governance", "Heimdall"],
)

def _get_client():
    from app.main import app as main_app
    return TestClient(main_app)

def _call_governance(build: HeimdallBuildRequest) -> dict:
    """
    Calls /governance/evaluate_all with a build-focused context.
    All values MUST be converted to strings (requirement of GovernanceEvaluationRequest).
    """
    g = build.governance_flags or {}

    data: Dict[str, Any] = {
        # Odin-ish strategic checks
        "active_verticals": str(g.get("active_verticals", 1)),
        "new_verticals": str(g.get("new_verticals", 0)),
        "estimated_annual_profit": str(g.get(
            "estimated_annual_profit",
            build.estimated_annual_profit_impact or 0,
        )),
        "complexity_score": str(g.get("complexity_score", build.complexity_score)),
        "time_to_break_even_months": str(g.get("time_to_break_even_months", 12)),
        "mission_critical": str(g.get(
            "mission_critical",
            build.strategic_importance >= 7,
        )),
        "distraction_score": str(g.get(
            "distraction_score",
            2 if build.strategic_importance >= 5 else 7,
        )),
        # Queen-ish capacity checks
        "hours_per_week": str(g.get("hours_per_week", 40)),
        "parallel_projects": str(g.get("parallel_projects", 1)),
        "uses_evenings": str(g.get("uses_evenings", False)),
        "uses_weekends": str(g.get("uses_weekends", False)),
        "sprint_weeks": str(g.get("sprint_weeks", 4)),
        "stress_level": str(g.get("stress_level", 6)),
        "chaos_factor": str(g.get("chaos_factor", 4.0)),
        # Loki-ish risk inversion
        "capital_at_risk": str(g.get("capital_at_risk", 0)),
        "worst_case_loss": str(g.get("worst_case_loss", 0)),
        "probability_of_ruin": str(g.get("probability_of_ruin", 0.01)),
        "correlation_with_portfolio": str(g.get("correlation_with_portfolio", 0.6)),
        "hidden_complexity_score": str(g.get(
            "hidden_complexity_score",
            build.complexity_score,
        )),
        # King-ish generic ROI / risk
        "purchase_price": str(g.get("purchase_price", "0")) if g.get("purchase_price") is not None else "0",
        "repairs": str(g.get("repairs", "0")) if g.get("repairs") is not None else "0",
        "arv": str(g.get("arv", "0")) if g.get("arv") is not None else "0",
        "roi": str(g.get("roi", "0")) if g.get("roi") is not None else "0",
        "predatory": str(g.get("predatory", False)),
        # Tyr-ish legal/ethics
        "requires_license_without_having_it": str(g.get(
            "requires_license_without_having_it",
            False,
        )),
        "tax_evasion": str(g.get("tax_evasion", False)),
        "fraudulent_misrepresentation": str(g.get(
            "fraudulent_misrepresentation",
            False,
        )),
        "recording_without_consent": str(g.get(
            "recording_without_consent",
            False,
        )),
        "exploits_vulnerable": str(g.get("exploits_vulnerable", False)),
        "misleading_marketing": str(g.get("misleading_marketing", False)),
        "missing_disclosures": str(g.get("missing_disclosures", False)),
    }

    # Allow raw flags to overwrite anything above (convert to strings if not already)
    for key, value in g.items():
        if key not in data or value is not None:
            data[key] = str(value) if value is not None else None

    body = {
        "context_type": "build_request",
        "data": data,
        "gods": None,
    }

    client = _get_client()
    resp = client.post("/api/governance/evaluate_all", json=body)
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"governance/evaluate_all failed for Heimdall build: "
            f"{resp.status_code} {resp.text}",
        )

    return resp.json()

def _call_builder(build: HeimdallBuildRequest) -> Optional[dict]:
    """
    Optionally calls the underlying builder API.

    We assume an endpoint like /api/builder/tasks exists as documented
    in AUTO_BUILDER_GUIDE.md. If it doesn't, we fail gracefully and
    simply return None.
    """
    # If your builder lives under a different path, adjust here.
    payload = {
        "title": build.title,
        "description": build.description,
        "priority": build.priority,
        "vertical": build.vertical,
        "metadata": {
            "estimated_hours": build.estimated_hours,
            "complexity_score": build.complexity_score,
            "estimated_annual_profit_impact": build.estimated_annual_profit_impact,
            "strategic_importance": build.strategic_importance,
            "scope": build.scope.model_dump(),
        },
    }

    client = _get_client()
    resp = client.post("/api/builder/tasks", json=payload)
    if resp.status_code not in (200, 201):
        # Graceful failure – we still return governance OK but no builder task.
        return None

    return resp.json()

@router.post(
    "/heimdall_build_request",
    response_model=HeimdallBuildResponse,
    status_code=status.HTTP_200_OK,
    summary="Governance-gated Heimdall auto-build request",
    description=(
        "Runs the full governance pantheon over a Heimdall build request. "
        "If governance approves, optionally forwards to /api/builder/tasks to "
        "create a build task. If any god issues a critical block, the builder "
        "is NOT called and accepted=False is returned."
    ),
)
def heimdall_build_request(build: HeimdallBuildRequest) -> HeimdallBuildResponse:
    # 1) Governance first
    governance_decision = _call_governance(build)

    if not governance_decision.get("overall_allowed", False):
        return HeimdallBuildResponse(
            accepted=False,
            governance=governance_decision,
            builder_task_created=False,
            builder_task_id=None,
            builder_raw_response=None,
            message="Governance blocked this Heimdall build request.",
        )

    # 2) Governance OK → attempt to create builder task
    builder_resp = _call_builder(build)

    if builder_resp is None:
        return HeimdallBuildResponse(
            accepted=True,
            governance=governance_decision,
            builder_task_created=False,
            builder_task_id=None,
            builder_raw_response=None,
            message="Governance approved, but builder task could not be created (or endpoint missing).",
        )

    task_id = (
        str(builder_resp.get("id"))
        if "id" in builder_resp
        else builder_resp.get("task_id")
    )

    return HeimdallBuildResponse(
        accepted=True,
        governance=governance_decision,
        builder_task_created=True,
        builder_task_id=str(task_id) if task_id is not None else None,
        builder_raw_response=builder_resp,
        message="Governance approved and builder task created.",
    )
