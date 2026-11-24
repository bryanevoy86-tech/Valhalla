"""Prospective disposable comparison recorded in the existing Foundry journal."""
from datetime import datetime, timedelta, timezone
import os
from typing import Annotated
from uuid import UUID

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from fastapi import HTTPException
from pydantic import AwareDatetime, Field, model_validator

from app.loki.evidence import artifact_digest
from app.schemas.market_intelligence import StrictModel


PLAN = "FOUNDRY_ECONOMIC_HOLDOUT_PLAN"
RESULT = "FOUNDRY_ECONOMIC_HOLDOUT_RESULT"
COMPARISON_RULE = "CONTRIBUTION_UP_REFUNDS_COSTS_AND_DOWNSIDE_NO_WORSE_V1"
Minor = Annotated[int, Field(strict=True, ge=0, le=100000000)]
Sha = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class Plan(StrictModel):
    training_outcome_sha256: Sha
    cohort_id: UUID
    case_ids: list[UUID] = Field(min_length=3, max_length=20)
    original_version: Sha
    revised_version: Sha
    revised_strategy: Annotated[str, Field(min_length=20, max_length=300)]
    observation_deadline: AwareDatetime
    maximum_loss_per_case_minor: Minor

    @model_validator(mode="after")
    def distinct(self):
        if self.original_version == self.revised_version or len(set(self.case_ids)) != len(self.case_ids):
            raise ValueError("Use distinct versions and unique paired cases")
        return self


class Arm(StrictModel):
    gross_minor: Minor
    refund_minor: Minor
    execution_cost_minor: Minor

    @model_validator(mode="after")
    def reconcile(self):
        if self.refund_minor > self.gross_minor:
            raise ValueError("Refund exceeds gross")
        return self


class Pair(StrictModel):
    case_id: UUID
    observed_at: AwareDatetime
    original: Arm
    revised: Arm


class Outcome(StrictModel):
    plan_sha256: Sha
    cohort_id: UUID
    cases: list[Pair] = Field(min_length=3, max_length=20)
    signature: Annotated[str, Field(pattern=r"^[a-f0-9]{128}$")]


def observer_key():
    raw = os.getenv("VALHALLA_OPERATING_HOLDOUT_OBSERVER_PUBLIC_KEY", "")
    try:
        return Ed25519PublicKey.from_public_bytes(bytes.fromhex(raw))
    except ValueError:
        raise HTTPException(503, "Independent holdout observer is unavailable") from None


def observation_message(outcome):
    return bytes.fromhex(artifact_digest(RESULT, outcome["plan_sha256"], outcome))


def freeze(run_id, request, lesson):
    now = datetime.now(timezone.utc)
    if not now < request.observation_deadline <= now + timedelta(days=7):
        raise HTTPException(409, "Holdout deadline must be prospective and at most seven days")
    if run_id in {request.cohort_id, *request.case_ids} or request.cohort_id in request.case_ids:
        raise HTTPException(409, "Holdout cohort and cases must be separate from training")
    baseline = artifact_digest("foundry_playbook_baseline", str(run_id), lesson["prediction"])
    revised = artifact_digest("foundry_playbook_revision", baseline, {"strategy": request.revised_strategy})
    if (request.original_version, request.revised_version) != (baseline, revised):
        raise HTTPException(409, "Holdout must pin the original forecast and exact revised strategy")
    return {
        **request.model_dump(mode="json"),
        "frozen_at": now.isoformat(),
        "observer_public_key": observer_key().public_bytes_raw().hex(),
        "metrics": ["contribution_minor", "refund_minor", "execution_cost_minor", "worst_case_contribution_minor"],
        "dataset": "INDEPENDENTLY_SIGNED_DISPOSABLE_PAIRED_HOLDOUT",
        "comparison_rule": COMPARISON_RULE,
        "promotion_rule": "FIXTURE_NEVER_PROMOTES_PRODUCTION",
    }


def score(plan, request, *, review_time):
    if plan["comparison_rule"] != COMPARISON_RULE:
        raise HTTPException(409, "Frozen holdout scoring rule is unavailable")
    if str(request.cohort_id) != plan["cohort_id"] or sorted(str(pair.case_id) for pair in request.cases) != sorted(plan["case_ids"]):
        raise HTTPException(409, "Holdout must contain exactly the frozen cases once")
    observed = datetime.now(timezone.utc)
    start = max(datetime.fromisoformat(plan["frozen_at"]), review_time)
    end = datetime.fromisoformat(plan["observation_deadline"])
    if observed > end or any(not start < case.observed_at <= observed for case in request.cases):
        raise HTTPException(409, "Holdout observation timing is ineligible")
    key = observer_key()
    if key.public_bytes_raw().hex() != plan["observer_public_key"]:
        raise HTTPException(409, "Holdout observer key was changed or revoked")
    try:
        key.verify(bytes.fromhex(request.signature), observation_message(request.model_dump(mode="json", exclude={"signature"})))
    except (InvalidSignature, ValueError):
        raise HTTPException(409, "Holdout observer signature is invalid") from None
    metrics = {}
    for name in ("original", "revised"):
        arms = [getattr(pair, name) for pair in request.cases]
        contributions = [arm.gross_minor - arm.refund_minor - arm.execution_cost_minor for arm in arms]
        metrics[name] = {
            "contribution_minor": sum(contributions), "refund_minor": sum(arm.refund_minor for arm in arms),
            "execution_cost_minor": sum(arm.execution_cost_minor for arm in arms),
            "worst_case_contribution_minor": min(contributions),
        }
    base, revised = metrics["original"], metrics["revised"]
    better = (revised["contribution_minor"] > base["contribution_minor"]
              and revised["refund_minor"] <= base["refund_minor"]
              and revised["execution_cost_minor"] <= base["execution_cost_minor"]
              and revised["worst_case_contribution_minor"] >= max(
                  base["worst_case_contribution_minor"], -plan["maximum_loss_per_case_minor"],
              ))
    return {"metrics": metrics, "paired_case_count": len(request.cases),
            "fixture_assessment": "BETTER_ON_FIXTURE" if better else "FAILED_ECONOMIC_RULE",
            "promotion": "REJECTED_NO_VERIFIED_REAL_OUTCOMES" if better else "REJECTED_ECONOMICS",
            "commercial_promotion_authorized": False}
