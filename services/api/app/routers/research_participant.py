"""Authenticated participant facade for the isolated research rehearsal."""
import hashlib
import hmac
import os
from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field, StrictBool
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent as Event
from app.routers.auth_weweb import _is_configured_owner, get_current_user, private_owner_response
from app.routers.customer_research import (
    Scoped, answer_participant, commit, current, enroll_participant, guarded, save, withdraw_participant,
)
from app.schemas.market_intelligence import StrictModel
from app.services import customer_research as research
from app.services.prime_business_execution import _emergency_stop_active, _event, _json
from app.services.specialist_triggers import outcome_scope_key
from app.users.models import AccountSettings, UserProfile

router = APIRouter(prefix="/api/weweb/customer-research")
NOTICE = {
    "version": research.PARTICIPANT_NOTICE,
    "text": (
        "Heimdall is Valhalla’s automated interviewer. This private rehearsal is voluntary and only accepts "
        "disposable accounts. It records your selected answers and consent for this round. It records no audio "
        "and permits no marketing follow-up. You can withdraw and erase your answers. The research worker "
        "purges answers and enrollment records 24 hours after the round closes. A pseudonymous opt-out "
        "remains until the disposable database is destroyed."
    ),
}
NOTICE_SHA = artifact_digest("research_notice", NOTICE["version"], NOTICE)


class Grant(Scoped):
    user_id: int = Field(strict=True, gt=0)


class Consent(StrictModel):
    consent: StrictBool
    notice_version: Literal["heimdall-participant-research-v1"]
    notice_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class Answer(StrictModel):
    step: Literal["problem", "authority", "effort", "interest"]
    answer: Literal["yes", "no", "unsure", "skip", "under_1h", "1_to_4h", "over_4h"]


def identity_secret():
    key = os.environ.get("VALHALLA_RESEARCH_IDENTITY_HMAC", "")
    if not research.enabled() or len(key.encode()) < 32:
        raise HTTPException(503, "Participant rehearsal unavailable")
    return key.encode()


def profile(db, subject):
    user = db.scalar(select(UserProfile).join(AccountSettings).where(
        UserProfile.user_id == subject,
        AccountSettings.account_locked.is_(False), AccountSettings.email_verified.is_(True),
    ))
    if (not user or not user.created_at or not user.email.endswith("@example.invalid")
            or _is_configured_owner(user.email)):
        raise HTTPException(403, "Verified disposable participant account required")
    return user


def identity(db, scope, user, *, establish=False):
    key = identity_secret()
    scope_key = outcome_scope_key(scope)
    event_id = f"research-id-{scope_key[:64]}"
    seal = hmac.new(key, f"research-namespace:{scope_key}".encode(), hashlib.sha256).hexdigest()
    row = db.scalar(select(Event).filter_by(event_id=event_id))
    if row is None and establish:
        _event(db, event_id=event_id, legacy_instance_id=scope["legacy_instance_id"],
               event_type="CUSTOMER_RESEARCH_IDENTITY_NAMESPACE", message="Disposable identity namespace initialized",
               payload={"scope_key": scope_key, "seal": seal})
    elif (row is None or row.event_type != "CUSTOMER_RESEARCH_IDENTITY_NAMESPACE"
            or _json(row.payload_json, {}) != {"scope_key": scope_key, "seal": seal}):
        raise HTTPException(503, "Research identity namespace unavailable")
    subject = f"{scope_key}:{user.user_id}:{user.created_at.isoformat()}"
    return hmac.new(key, subject.encode(), hashlib.sha256).hexdigest()


@router.post("/{round_id}/grant", dependencies=[Depends(require_prime_control_key)])
def grant(round_id: UUID, request: Grant, db: Session = Depends(get_db)):
    row, state = current(db, request, round_id, write=True)
    if not state["design"].get("identity_bound"):
        raise HTTPException(409, "Identity-bound research round required")
    key = identity(db, state["scope"], profile(db, request.user_id), establish=True)
    if db.scalar(select(Event.id).filter_by(event_id=research.suppression_key(key))):
        raise HTTPException(409, "Enrollment unavailable")
    grants = state.setdefault("participant_grants", [])
    if key not in grants:
        if len(grants) >= state["design"]["max_enrollments"]:
            raise HTTPException(409, "Enrollment cap reached")
        grants.append(key)
        save(db, row, state)
    return private_owner_response({"status": "GRANTED", "sent": False})


def participant(db, round_id, session, *, write=False):
    identity_secret()
    subject = session.get("user_id")
    if type(subject) is not int:
        raise HTTPException(403, "Participant session required")
    user = profile(db, subject)
    if session.get("sub") != user.email:
        raise HTTPException(403, "Participant session required")
    query = select(Event).filter_by(event_id=research.event_key(round_id), event_type=research.ROUND)
    row = db.scalar(query.with_for_update() if write else query)
    if row is None:
        raise HTTPException(404, "Research invitation unavailable")
    state = research.validate_state(row)
    if not state["design"].get("identity_bound") or not state.get("participant_grants"):
        raise HTTPException(404, "Research invitation unavailable")
    key = identity(db, state["scope"], user)
    if key not in state["participant_grants"]:
        raise HTTPException(404, "Research invitation unavailable")
    return row, state, key


@router.get("/{round_id}")
def status(round_id: UUID, session: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    _, state, key = participant(db, round_id, session)
    record = state["participants"].get(key)
    if (record and record["withdrawn"]) or db.scalar(select(Event.id).filter_by(
        event_id=research.suppression_key(key)
    )):
        result = {"status": "WITHDRAWN"}
    elif research.now() >= datetime.fromisoformat(state["expires_at"]):
        result = {"status": "CLOSED"}
    elif _emergency_stop_active(db):
        result = {"status": "PAUSED"}
    else:
        guarded(db, Scoped(scope=state["scope"]))
        if not state["invitation_prepared"]:
            raise HTTPException(404, "Research invitation unavailable")
        result = (research.prompt(record["answers"], state["design"]) if record
                  else {"status": "CONSENT_REQUIRED", "notice": NOTICE, "notice_sha256": NOTICE_SHA})
    return private_owner_response(result)


@router.post("/{round_id}/enroll")
def enroll(round_id: UUID, request: Consent, session: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if not request.consent or request.notice_sha256 != NOTICE_SHA:
        raise HTTPException(422, "Current affirmative research consent required")
    row, state, key = participant(db, round_id, session, write=True)
    require_open(db, state)
    return enroll_participant(db, row, state, key, NOTICE["version"], NOTICE_SHA)


def require_open(db, state):
    if research.now() >= datetime.fromisoformat(state["expires_at"]):
        raise HTTPException(410, "Research round closed")
    guarded(db, Scoped(scope=state["scope"]))


@router.post("/{round_id}/answer")
def answer(round_id: UUID, request: Answer, session: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    row, state, key = participant(db, round_id, session, write=True)
    require_open(db, state)
    return answer_participant(db, row, state, key, request.step, request.answer)


@router.post("/{round_id}/withdraw")
def withdraw(round_id: UUID, session: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    row, state, key = participant(db, round_id, session, write=True)
    if key in state["participants"]:
        return withdraw_participant(db, row, state, key)
    event_id = research.suppression_key(key)
    if db.scalar(select(Event.id).filter_by(event_id=event_id)) is None:
        _event(db, event_id=event_id, legacy_instance_id=state["scope"]["legacy_instance_id"],
               event_type="CUSTOMER_RESEARCH_SUPPRESSION_FIXTURE", message="Research invitation declined", payload={})
        commit(db)
    return private_owner_response({"status": "WITHDRAWN", "answers_removed": True, "suppressed": True})


def purge_if_due(db, row, state):
    if (not state["design"].get("identity_bound") or state.get("purged")
            or research.now() < datetime.fromisoformat(state["expires_at"]) + timedelta(hours=24)):
        return False
    joins = [f"research-join-{key}" for key in state.get("participant_grants", [])]
    if joins:
        db.query(Event).filter(Event.event_id.in_(joins), Event.event_type == "CUSTOMER_RESEARCH_JOIN_FIXTURE").delete(
            synchronize_session=False)
    state.update(participants={}, participant_grants=[], purged=True)
    save(db, row, state)
    return True
