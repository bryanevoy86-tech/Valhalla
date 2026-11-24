"""Disposable first-party research intake with structured, adaptive interviews."""
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import inspect, select, update

from app.heimdall.authority import is_live
from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent as Event
from app.services.prime_business_execution import _event
from app.services.specialist_triggers import outcome_scope_key

ROUND = "CUSTOMER_RESEARCH_FIXTURE"
TYPE = "customer_research"
NOTICE = "heimdall-structured-research-v1"
ROLES = {"ODIN", "FREYJA", "NORNS", "NJORD", "TYR", "FORSETI", "MIMIR", "HEIMDALL"}
DISCLOSURE = (
    "Heimdall is Valhalla's automated research interviewer. Participation is optional. "
    "This disposable rehearsal accepts structured fixture responses only. "
    "It records research answers, does not record audio, and provides withdrawal. "
    "Consent covers this research only."
)
QUESTIONS = {
    "problem": ("Did this workflow cause recurring work in the past 30 days?", ("yes", "no", "skip")),
    "authority": ("Are you authorized to evaluate a purchase for this workflow?", ("yes", "no", "skip")),
    "effort": ("How much team time did this workflow take in a typical week?", ("under_1h", "1_to_4h", "over_4h", "skip")),
    "interest": ("At the disclosed CAD reference price, would you consider a separate pilot discussion?",
                 ("yes", "no", "unsure", "skip")),
}


def enabled():
    return (os.environ.get("VALHALLA_CUSTOMER_RESEARCH_REHEARSAL") == "1" and not is_live()
            and os.environ.get("APP_ENV", "").lower() in {"dev", "test", "sandbox"}
            and os.environ.get("ENV", "").lower() in {"", "dev", "test", "sandbox"})


def now():
    return datetime.now(timezone.utc)


def event_key(round_id):
    return f"research-{round_id}"


def participant_key(scope, token):
    return hashlib.sha256(f"{outcome_scope_key(scope)}:{token}".encode()).hexdigest()


def suppression_key(participant):
    return f"suppress-{participant}"


def validate_state(row):
    try:
        state = json.loads(row.payload_json)
        seal = state.pop("state_sha256")
        if (seal != artifact_digest(ROUND, row.event_id, state)
                or row.legacy_instance_id != state["scope"]["legacy_instance_id"]):
            raise ValueError("Research digest or scope mismatch")
    except (AttributeError, TypeError, ValueError, KeyError):
        raise HTTPException(409, "Research state integrity check failed") from None
    return state


def load(db, round_id, scope, *, lock=False):
    query = select(Event).filter_by(event_id=event_key(round_id), event_type=ROUND)
    if lock:
        query = query.with_for_update()
    row = db.scalar(query)
    if row is None or row.legacy_instance_id != scope["legacy_instance_id"]:
        raise HTTPException(404, "Research round unavailable")
    state = validate_state(row)
    if state["scope"] != scope:
        raise HTTPException(404, "Research round unavailable")
    return row, state


def sealed(round_id, state):
    return {**state, "state_sha256": artifact_digest(ROUND, event_key(round_id), state)}


def start(db, request, scope):
    expiry = now() + timedelta(hours=request.duration_hours)
    state = {
        "scope": scope, "round_id": str(request.round_id), "design": request.model_dump(mode="json"),
        "expires_at": expiry.isoformat(), "participants": {}, "invitation_prepared": False,
    }
    _event(db, event_id=event_key(request.round_id), legacy_instance_id=scope["legacy_instance_id"],
           event_type=ROUND, message="Disposable customer research round",
           payload=sealed(request.round_id, state))
    return state


def save(db, row, state):
    payload = json.dumps(sealed(state["round_id"], state), sort_keys=True, separators=(",", ":"))
    match = db.execute(update(Event).where(Event.id == row.id, Event.payload_json == row.payload_json)
                       .values(payload_json=payload))
    if match.rowcount != 1:
        raise HTTPException(409, "Research state changed, reread the current step")


def next_step(answers):
    if "problem" not in answers:
        return "problem"
    if answers["problem"] != "yes":
        return None
    if "authority" not in answers:
        return "authority"
    if answers["authority"] != "yes":
        return None
    if "effort" not in answers:
        return "effort"
    return "interest" if "interest" not in answers else None


def prompt(answers, design):
    step = next_step(answers)
    if step is None:
        return {"status": "COMPLETED"}
    question, options = QUESTIONS[step]
    if step == "problem":
        topics = {"fleet_records": "fleet maintenance records", "contractor_quotes": "contractor quoting",
                  "workflow_automation": "a manual business workflow"}
        question = f"Research topic: {topics[design['topic']]}. {question}"
    if step == "interest":
        price = design["reference_price_minor"]
        question = f"{question} Research reference CAD {price // 100}.{price % 100:02d}. No purchase or offer."
    return {"status": "INTERVIEW", "step": step, "question": question, "options": options}


def summary(state):
    participants = list(state["participants"].values())
    active = [x["answers"] for x in participants if not x["withdrawn"]]
    completed = [answers for answers in active if next_step(answers) is None]
    qualified = [answers for answers in completed if answers.get("authority") == "yes"]
    data = {
        "basis": "DISPOSABLE_RESEARCH_FIXTURE", "scope": state["scope"], "round_id": state["round_id"],
        "expires_at": state["expires_at"], "notice_version": NOTICE,
        "reference_price_minor": state["design"]["reference_price_minor"],
        "topic": state["design"]["topic"],
        "sample_source": "VOLUNTARY_SINGLE_CHANNEL", "enrolled": len(participants),
        "withdrawn": len(participants) - len(active), "completed": len(completed),
        "qualified": len(qualified), "stated_interest": sum(x.get("interest") == "yes" for x in qualified),
        "paid_outcomes_verified": False, "actual_customers_verified": False,
        "verified_cac_minor": None, "external_action_authorized": False,
    }
    return {**data, "study_sha256": artifact_digest(TYPE, state["round_id"], sealed(state["round_id"], state))}


def observe(db, scope, role):
    if not enabled() or role not in ROLES or not inspect(db.connection()).has_table(Event.__tablename__):
        return None
    rows = db.scalars(select(Event).filter_by(event_type=ROUND, legacy_instance_id=scope["legacy_instance_id"])
                      .order_by(Event.id.desc()).limit(30))
    for row in rows:
        state = validate_state(row)
        if state["scope"] == scope:
            if datetime.fromisoformat(state["expires_at"]) <= now():
                return None
            result = summary(state)
            # Specialist journals retain only source grade and checks, without sample counts or answers.
            checks = {
                "FREYJA": "Verify repeated pain and independent buyer authority.",
                "ODIN": "Compare segment fit against separately sourced alternatives.",
                "NORNS": "Do not generalize from voluntary or small samples.",
                "NJORD": "Require observed acquisition cost, settlement and delivery economics.",
                "TYR": "Recheck purpose and consent before any different use.",
                "FORSETI": "Check provenance, repeat enrollment and corroboration.",
                "MIMIR": "Keep fixture learning separate from paid customer outcomes.",
                "HEIMDALL": "Abstain from commercial selection and request first-party evidence.",
            }
            return {"basis": result["basis"], "study_sha256": result["study_sha256"],
                    "check": checks[role], "external_action_authorized": False}
    return None
