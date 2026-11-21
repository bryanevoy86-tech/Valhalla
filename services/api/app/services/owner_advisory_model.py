"""Send only explicitly classified synthetic text through the approved gateway."""
from datetime import datetime, timezone
import os

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError

from app.models.go_live_state import GoLiveState
from app.models.model_provider import ModelProvider
from app.models.owner_conversation import OwnerInferenceAttempt, OwnerInferenceQuota


SYSTEM = (
    "You are Heimdall Prime's advisory interface for synthetic test input. "
    "Distinguish evidence from assumptions. You cannot execute actions, grant approvals, "
    "contact third parties or claim work was completed."
)
PROVIDERS = {
    "openai": ("https://api.openai.com/v1/chat/completions", "VALHALLA_OWNER_CHAT_OPENAI_KEY"),
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "VALHALLA_OWNER_CHAT_GROQ_KEY"),
}


def reserve_attempt(db, turn_id, vendor, model, limit):
    dialect = db.get_bind().dialect.name
    if dialect not in {"postgresql", "sqlite"}:
        return None
    if db.get(OwnerInferenceAttempt, turn_id) is not None:
        raise HTTPException(409, "An advisory attempt already exists for this turn")
    day = datetime.now(timezone.utc).date().isoformat()
    insert = postgres_insert if dialect == "postgresql" else sqlite_insert
    quota = insert(OwnerInferenceQuota).values(day=day, requests=1)
    quota = quota.on_conflict_do_update(
        index_elements=[OwnerInferenceQuota.day],
        set_={"requests": OwnerInferenceQuota.requests + 1},
        where=OwnerInferenceQuota.requests < limit,
    ).returning(OwnerInferenceQuota.day)
    if db.scalar(quota) is None:
        db.rollback()
        return None
    attempt = OwnerInferenceAttempt(turn_id=turn_id, day=day, vendor=vendor, model=model, status="reserved")
    db.add(attempt)
    try:
        db.commit()
    except IntegrityError:
        # A concurrent replay must undo its quota increment and make no call.
        db.rollback()
        raise HTTPException(409, "An advisory attempt already exists for this turn") from None
    return attempt


def advisory_reply(db, turn_id, message, data_class):
    if data_class != "SYNTHETIC" or len(message.encode("utf-8")) > 2000:
        return None
    if (os.getenv("VALHALLA_OWNER_CHAT_INFERENCE_ENABLED") != "1"
            or os.getenv("VALHALLA_OWNER_CHAT_RELEASE_APPROVED") != "1"
            or os.getenv("VALHALLA_EMERGENCY_STOP", "").strip().lower() in {"1", "true", "yes", "on"}):
        return None
    control = db.get(GoLiveState, 1)
    if control is None or control.kill_switch_engaged is not False:
        return None
    vendor = os.getenv("VALHALLA_OWNER_CHAT_VENDOR", "openai").strip().lower()
    if vendor not in PROVIDERS:
        return None
    if vendor == "groq" and os.getenv("VALHALLA_OWNER_CHAT_GROQ_FREE_PLAN_CONFIRMED") != "1":
        return None
    # No paid fallback or paid provider authorization from a model registry entry.
    if vendor == "openai" and os.getenv("VALHALLA_OWNER_CHAT_OPENAI_SPEND_APPROVED") != "1":
        return None
    try:
        limit = int(os.getenv("VALHALLA_OWNER_CHAT_DAILY_REQUEST_LIMIT", "0"))
    except ValueError:
        return None
    endpoint, key_name = PROVIDERS[vendor]
    key = os.getenv(key_name, "").strip()
    allowed_model = os.getenv("VALHALLA_OWNER_CHAT_MODEL", "").strip()
    if not key or not 1 <= len(allowed_model) <= 160 or not 1 <= limit <= 50:
        return None
    providers = db.scalars(select(ModelProvider).where(
        ModelProvider.active.is_(True), ModelProvider.default_for_heimdall.is_(True))).all()
    if len(providers) != 1:
        return None
    provider = providers[0]
    config = provider.config or {}
    if provider.vendor.lower() != vendor or not isinstance(config, dict) or config.get("model") != allowed_model:
        return None
    attempt = reserve_attempt(db, turn_id, vendor, allowed_model, limit)
    if attempt is None:
        return None

    reply = None
    try:
        with httpx.Client(timeout=25.0, follow_redirects=False, trust_env=False) as client:
            response = client.post(
                endpoint, headers={"Authorization": "Bearer " + key},
                json={"model": allowed_model,
                      "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": message}],
                      "max_completion_tokens": 500},
            )
            response.raise_for_status()
            result = response.json()
            choice = result["choices"][0]
            candidate = choice["message"]["content"]
            if (isinstance(candidate, str) and candidate.strip() and len(candidate) <= 16000
                    and not choice["message"].get("tool_calls") and choice.get("finish_reason") == "stop"):
                reply = candidate
            usage = result.get("usage")
            if isinstance(usage, dict):
                for name in ("prompt_tokens", "completion_tokens"):
                    value = usage.get(name)
                    if type(value) is int and 0 <= value <= 1_000_000:
                        setattr(attempt, name, value)
    except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError):
        pass
    attempt.status = "answered" if reply is not None else "unavailable"
    db.commit()
    if reply is None:
        return None
    return reply, {"source": "owner_advisory_model", "model_connected": True,
                   "model": allowed_model, "provider": vendor, "data_class": "SYNTHETIC",
                   "context_turn_ids": [], "verified_execution": False}
