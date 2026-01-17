# services/api/app/routers/governance_tyr.py

from __future__ import annotations

from typing import List

from fastapi import APIRouter, status

from app.schemas.governance import (
    TyrPolicy,
    KingEvaluationContext,  # generic context
    KingDecision,           # generic decision shape
)

router = APIRouter(
    prefix="/governance",
    tags=["Governance", "Tyr"],
)

TYR_POLICY = TyrPolicy()


def _to_bool(val) -> bool:
    """Convert string or value to boolean."""
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes")
    return bool(val)


def evaluate_legal(policy: TyrPolicy, data: dict) -> List[str]:
    """
    Checks legal red lines.
    All signals are boolean flags in the payload.
    """
    reasons: List[str] = []

    if policy.legal.forbid_unlicensed_practice and _to_bool(data.get("requires_license_without_having_it")):
        reasons.append(
            "Action requires a license that is not currently held. Tyr forbids unlicensed practice."
        )

    if policy.legal.forbid_tax_evasion and _to_bool(data.get("tax_evasion")):
        reasons.append("Action is flagged as tax evasion. Tyr forbids hiding income or fabricating expenses.")

    if policy.legal.forbid_fraudulent_misrepresentation and _to_bool(data.get("fraudulent_misrepresentation")):
        reasons.append("Action involves fraudulent misrepresentation of material facts.")

    if policy.legal.require_written_consent_for_recording and _to_bool(data.get("recording_without_consent")):
        reasons.append(
            "Recording without proper consent in a jurisdiction that requires consent. "
            "Tyr requires written consent for recordings."
        )

    return reasons


def evaluate_ethics(policy: TyrPolicy, data: dict) -> List[str]:
    """
    Checks core ethical red lines.
    """
    reasons: List[str] = []

    if policy.ethics.forbid_exploiting_vulnerable and _to_bool(data.get("exploits_vulnerable")):
        reasons.append("Deal explicitly exploits vulnerable parties. Tyr forbids this.")

    if policy.ethics.forbid_misleading_marketing and _to_bool(data.get("misleading_marketing")):
        reasons.append("Marketing is flagged as misleading or deceptive.")

    if policy.ethics.require_clear_disclosures and _to_bool(data.get("missing_disclosures")):
        reasons.append("Required risk/term/conflict disclosures are missing or incomplete.")

    return reasons


@router.post(
    "/tyr/evaluate",
    response_model=KingDecision,
    status_code=status.HTTP_200_OK,
    summary="Tyr evaluation: legal & ethical hard lines",
    description=(
        "Tyr enforces hard legal and ethical red lines. If a plan, deal, or operation crosses "
        "these lines, Tyr will deny approval regardless of profit or strategy."
    ),
)
def evaluate_tyr(payload: KingEvaluationContext) -> KingDecision:
    data = payload.data
    policy = TYR_POLICY

    legal_reasons = evaluate_legal(policy, data)
    ethics_reasons = evaluate_ethics(policy, data)

    all_reasons = legal_reasons + ethics_reasons

    if not all_reasons:
        return KingDecision(
            allowed=True,
            severity="info",
            reasons=[],
            notes="Tyr sees no legal or ethical red-line violations.",
        )

    # Any Tyr violation is critical by default
    severity = "critical"
    allowed = False

    return KingDecision(
        allowed=allowed,
        severity=severity,
        reasons=all_reasons,
        notes="Tyr denies; legal or ethical red lines would be crossed.",
    )
