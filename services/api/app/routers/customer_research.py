"""Prime-controlled, disposable autonomous customer interview API."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field, StrictBool, UUID4
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.loki.evidence import artifact_digest
from app.loki.models import LokiReview, LokiReviewStatus
from app.loki.review_service import verdict
from app.loki.schemas import LokiReviewCreate
from app.models.completion_registry import LegacyOrchestrationEvent as Event
from app.routers.auth_weweb import private_owner_response
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services import customer_research as research
from app.services.economic_control import require_no_containment
from app.services.prime_business_execution import _check_legacy, _emergency_stop_active, _event, _json, require_owner_mandate_key

router = APIRouter(prefix="/api/prime/customer-research/rehearsal",
                   dependencies=[Depends(require_prime_control_key)])


class Scoped(StrictModel):
    scope: MarketScope


class Start(Scoped):
    round_id: UUID4
    topic: Literal["fleet_records", "contractor_quotes", "workflow_automation"]
    duration_hours: int = Field(strict=True, ge=1, le=336)
    max_enrollments: int = Field(strict=True, ge=1, le=24)
    reference_price_minor: int = Field(strict=True, gt=0, le=1_000_000)


class Enrollment(Scoped):
    token: UUID4
    consent: StrictBool
    notice_version: Literal["heimdall-structured-research-v1"]


class Answer(Scoped):
    token: UUID4
    step: Literal["problem", "authority", "effort", "interest"]
    answer: Literal["yes", "no", "unsure", "skip", "under_1h", "1_to_4h", "over_4h"]


class Participant(Scoped):
    token: UUID4


def guarded(db, request, *, withdrawal=False):
    if not research.enabled() or not inspect(db.connection()).has_table(Event.__tablename__):
        raise HTTPException(503, "Disposable customer research disabled")
    scope = request.scope.model_dump()
    if not withdrawal:
        if _emergency_stop_active(db):
            raise HTTPException(503, "Research paused")
        _check_legacy(db, **scope)
        require_no_containment(db, scope)
    return scope


def current(db, request, round_id, *, write=False, withdrawal=False):
    scope = guarded(db, request, withdrawal=withdrawal)
    row, state = research.load(db, round_id, scope, lock=write)
    if not withdrawal and research.now().isoformat() >= state["expires_at"]:
        raise HTTPException(409, "Research round expired")
    return row, state


def commit(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Research identity already in use") from None


def save(db, row, state):
    research.save(db, row, state)
    commit(db)


def participant_key(state, request):
    return research.participant_key(state["scope"], request.token)


@router.post("/rounds", dependencies=[Depends(require_owner_mandate_key)])
def open_round(request: Start, db: Session = Depends(get_db)):
    scope = guarded(db, request)
    prior = db.scalar(select(Event).filter_by(event_id=research.event_key(request.round_id)))
    if prior is None:
        state = research.start(db, request, scope)
        commit(db)
    else:
        _, state = research.load(db, request.round_id, scope)
        if state["design"] != request.model_dump(mode="json"):
            raise HTTPException(409, "Research round parameters differ")
    return private_owner_response(research.summary(state))


@router.post("/{round_id}/invitation")
def prepare_invitation(round_id: UUID, request: Scoped, db: Session = Depends(get_db)):
    row, state = current(db, request, round_id, write=True)
    if not state["invitation_prepared"]:
        state["invitation_prepared"] = True
        save(db, row, state)
    return private_owner_response({"notice": research.DISCLOSURE, "notice_version": research.NOTICE,
                                   "route": "VOLUNTARY_INBOUND_FIXTURE", "sent": False})


@router.post("/{round_id}/enroll")
def enroll(round_id: UUID, request: Enrollment, db: Session = Depends(get_db)):
    if not request.consent:
        raise HTTPException(422, "Affirmative research consent required")
    row, state = current(db, request, round_id, write=True)
    participants = state["participants"]
    key = participant_key(state, request)
    suppressed = db.scalar(select(Event.id).filter_by(event_id=research.suppression_key(key)))
    if not state["invitation_prepared"] or suppressed or participants.get(key, {}).get("withdrawn"):
        raise HTTPException(409, "Enrollment unavailable")
    if key not in participants:
        if len(participants) >= state["design"]["max_enrollments"]:
            raise HTTPException(409, "Enrollment cap reached")
        enrollment_id = f"research-join-{key}"
        if db.scalar(select(Event.id).filter_by(event_id=enrollment_id)) is not None:
            raise HTTPException(409, "Research token already used")
        participants[key] = {"notice_version": research.NOTICE, "consented_at": research.now().isoformat(),
                             "withdrawn": False, "answers": {}}
        _event(db, event_id=enrollment_id, legacy_instance_id=state["scope"]["legacy_instance_id"],
               event_type="CUSTOMER_RESEARCH_JOIN_FIXTURE", message="Research token consumed", payload={})
        save(db, row, state)
    return private_owner_response(research.prompt(participants[key]["answers"], state["design"]))


@router.post("/{round_id}/answer")
def answer(round_id: UUID, request: Answer, db: Session = Depends(get_db)):
    row, state = current(db, request, round_id, write=True)
    key = participant_key(state, request)
    participant = state["participants"].get(key)
    if not participant or participant["withdrawn"] or db.scalar(select(Event.id).filter_by(
        event_id=research.suppression_key(key)
    )):
        raise HTTPException(409, "Current research consent required")
    answers = participant["answers"]
    if answers.get(request.step) != request.answer:
        if (request.step != research.next_step(answers) or request.answer not in research.QUESTIONS[request.step][1]):
            raise HTTPException(409, "Answer does not match the current interview step")
        answers[request.step] = request.answer
        save(db, row, state)
    return private_owner_response(research.prompt(answers, state["design"]))


@router.post("/{round_id}/withdraw")
def withdraw(round_id: UUID, request: Participant, db: Session = Depends(get_db)):
    row, state = current(db, request, round_id, write=True, withdrawal=True)
    key = participant_key(state, request)
    participant = state["participants"].get(key)
    if not participant:
        raise HTTPException(404, "Enrollment unavailable")
    if not participant["withdrawn"]:
        state["participants"][key] = {"withdrawn": True, "answers": {}}
        event_id = research.suppression_key(key)
        if db.scalar(select(Event.id).filter_by(event_id=event_id)) is None:
            _event(db, event_id=event_id, legacy_instance_id=state["scope"]["legacy_instance_id"],
                   event_type="CUSTOMER_RESEARCH_SUPPRESSION_FIXTURE", message="Research withdrawn", payload={})
        save(db, row, state)
    return private_owner_response({"status": "WITHDRAWN", "answers_removed": True, "suppressed": True})


def review_payload(state):
    # This receipt carries aggregate synthetic counts only.
    material = research.summary(state)
    return {**material, "disposition": "ABSTAIN_PENDING_GENUINE_EVIDENCE"}


@router.post("/{round_id}/review")
def queue_review(round_id: UUID, request: Scoped, db: Session = Depends(get_db)):
    from app.routers.loki import create_loki_review

    _, state = current(db, request, round_id)
    material = review_payload(state)
    review = create_loki_review(LokiReviewCreate(
        input_source="prime-customer-research-rehearsal", artifact_type=research.TYPE,
        heimdall_reference_id=str(round_id), raw_input=material,
    ), db)
    return private_owner_response({
        "review_id": review.id, "artifact_sha256": review.artifact_sha256, "evidence": material,
    })


@router.post("/{round_id}/decision")
def next_decision(round_id: UUID, request: Scoped, db: Session = Depends(get_db)):
    _, state = current(db, request, round_id, write=True)
    material = review_payload(state)
    digest = artifact_digest(research.TYPE, str(round_id), material)
    review = db.scalar(select(LokiReview).filter_by(artifact_type=research.TYPE, artifact_sha256=digest))
    if review is None:
        raise HTTPException(409, "Current independent research review required")
    verified = verdict(db, review)
    result = {"decision": material["disposition"], "review_id": str(review.id), "artifact_sha256": digest,
              "independent_result_sha256": verified.result_sha256, "blockers": verified.key_risks,
              "external_action_authorized": False}
    event_id = f"research-decision-{digest[:52]}"
    prior = db.scalar(select(Event).filter_by(event_id=event_id))
    if prior is not None:
        return private_owner_response(_json(prior.payload_json, {}))
    _event(db, event_id=event_id, legacy_instance_id=state["scope"]["legacy_instance_id"],
           event_type="CUSTOMER_RESEARCH_DECISION", message="Bounded Prime research decision", payload=result)
    commit(db)
    return private_owner_response(result)


@router.post("/{round_id}/advance")
def advance(round_id: UUID, request: Scoped, db: Session = Depends(get_db)):
    """Prime's bounded polling entry point for invitations, review and abstention."""
    _, state = current(db, request, round_id, write=True)
    if not state["invitation_prepared"]:
        return prepare_invitation(round_id, request, db)
    material = review_payload(state)
    if not material["completed"]:
        return private_owner_response({"status": "WAITING_FOR_VOLUNTARY_ANSWERS"})
    digest = artifact_digest(research.TYPE, str(round_id), material)
    review = db.scalar(select(LokiReview).filter_by(artifact_type=research.TYPE, artifact_sha256=digest))
    if review is None:
        return queue_review(round_id, request, db)
    if review.status != LokiReviewStatus.COMPLETED:
        return private_owner_response({"status": "WAITING_FOR_INDEPENDENT_REVIEW"})
    return next_decision(round_id, request, db)
