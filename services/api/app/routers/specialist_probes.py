"""Owner-authorized Groq synthetic role probes. Disabled without staged release."""
import os
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.models.go_live_state import GoLiveState
from app.models.owner_conversation import OwnerInferenceAttempt
from app.models.specialist_probe import SpecialistProbe
from app.pantheon.roles import Role
from app.routers.provider_evidence import SUITE, recommend
from app.services.owner_advisory_model import PROVIDERS, reserve_attempt
from app.services.prime_business_execution import require_owner_mandate_key


router = APIRouter(
    prefix="/api/prime/provider-intelligence", tags=["specialist-staging"],
    dependencies=[Depends(require_prime_control_key), Depends(require_owner_mandate_key)],
)


class ProbeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    probe_id: UUID
    role: Role
    provider_id: int = Field(gt=0)
    case_id: str = Field(min_length=1, max_length=80)


def _receipt(row, attempt):
    return {
        "probe_id": row.id, "role": row.role, "provider_id": row.provider_id, "model": row.model,
        "case_id": row.case_id, "result": row.result, "data_class": "FIXED_SYNTHETIC_CASE",
        "prompt_tokens": attempt.prompt_tokens if attempt else None,
        "completion_tokens": attempt.completion_tokens if attempt else None,
        "billing_verified": False, "execution_authorized": False,
    }


@router.post("/stage-probes", status_code=201)
def run_probe(payload: ProbeIn, db: Session = Depends(get_db)):
    if (os.getenv("VALHALLA_SPECIALIST_STAGING_AUTHORIZED") != "1"
            or os.getenv("VALHALLA_SPECIALIST_GROQ_FREE_PLAN_CONFIRMED") != "1"
            or os.getenv("VALHALLA_EMERGENCY_STOP", "").strip().lower() in {"1", "true", "yes", "on"}):
        raise HTTPException(503, "Specialist inference is disabled")
    if payload.case_id not in SUITE:
        raise HTTPException(422, "Unknown synthetic case")
    schema = inspect(db.connection())
    if any(not schema.has_table(name) for name in (
        "prime_specialist_probes", "prime_provider_evidence", "model_providers", "go_live_state",
        "prime_owner_inference_attempts", "prime_owner_inference_quotas",
    )):
        raise HTTPException(503, "Specialist staging schema unavailable")
    control = db.get(GoLiveState, 1)
    if control is None or control.kill_switch_engaged is not False or control.go_live_enabled is not False:
        raise HTTPException(503, "Specialist probe requires cleared staging controls")
    existing = db.get(SpecialistProbe, payload.probe_id)
    if existing is not None:
        if (existing.role, existing.provider_id, existing.case_id) != (payload.role, payload.provider_id, payload.case_id):
            raise HTTPException(409, "Probe ID already used")
        return _receipt(existing, db.get(OwnerInferenceAttempt, payload.probe_id))

    prefix = "VALHALLA_LOKI" if payload.role == "LOKI" else "VALHALLA_SPECIALIST"
    key = os.getenv(prefix + "_GROQ_KEY", "").strip()
    model = os.getenv(prefix + "_GROQ_MODEL", "").strip()
    other = "VALHALLA_SPECIALIST" if payload.role == "LOKI" else "VALHALLA_LOKI"
    if not key or not model or key in {
        os.getenv(other + "_GROQ_KEY"), os.getenv("VALHALLA_OWNER_CHAT_GROQ_KEY"),
        os.getenv("VALHALLA_PRIME_CONTROL_KEY"), os.getenv("VALHALLA_LOKI_REVIEWER_KEY"),
        os.getenv("VALHALLA_OWNER_MANDATE_KEY"),
    }:
        raise HTTPException(503, "Independent specialist provider configuration is unavailable")
    try:
        limit = int(os.getenv("VALHALLA_SPECIALIST_DAILY_REQUEST_LIMIT", "0"))
    except ValueError:
        limit = 0
    if not 1 <= limit <= 10:
        raise HTTPException(503, "Stage probe budget unavailable")

    eligible = recommend(payload.role, "SYNTHETIC", db)["candidates"]
    if not any(item["provider_id"] == payload.provider_id and item["vendor"] == "groq" and item["model"] == model
               for item in eligible):
        raise HTTPException(409, "Provider lacks current synthetic evidence for this role")
    row = SpecialistProbe(id=payload.probe_id, role=payload.role, provider_id=payload.provider_id,
                          model=model, case_id=payload.case_id, result="reserved")
    db.add(row)
    attempt = reserve_attempt(db, payload.probe_id, "groq", model, limit)
    if attempt is None:
        raise HTTPException(429, "Stage probe budget exhausted")
    prompt, expected = SUITE[payload.case_id]
    row.result = "unavailable"
    try:
        with httpx.Client(timeout=12, follow_redirects=False, trust_env=False) as client:
            response = client.post(PROVIDERS["groq"][0], headers={"Authorization": "Bearer " + key}, json={
                "model": model, "max_completion_tokens": 64, "messages": [
                    {"role": "system", "content": "Return exactly one label: REVIEW, ABSTAIN, BLOCK, or ADVISE."},
                    {"role": "user", "content": prompt},
                ],
            })
            response.raise_for_status()
            body = response.json()
            choice = body["choices"][0]
            if choice.get("finish_reason") == "stop" and not choice["message"].get("tool_calls"):
                content = choice["message"].get("content")
                row.result = "pass" if isinstance(content, str) and content.strip() == expected else "fail"
            usage = body.get("usage")
            if isinstance(usage, dict):
                for name in ("prompt_tokens", "completion_tokens"):
                    value = usage.get(name)
                    if type(value) is int and 0 <= value <= 1_000_000:
                        setattr(attempt, name, value)
    except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError, AttributeError):
        pass
    attempt.status = row.result
    db.commit()
    return _receipt(row, attempt)
