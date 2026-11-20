"""Private closer scripts and durable operator notes."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.models.closer_session import CloserSession
from app.routers.closing_playbook import get_closing_playbook
from app.schemas.closer_engine import (
    CloserFeedbackRequest,
    CloserFeedbackResponse,
    CloserNextBlockRequest,
    CloserNextBlockResponse,
    CloserSessionContext,
    CloserSessionStartRequest,
    CloserSessionStartResponse,
)

router = APIRouter(prefix="/closer", tags=["CloserEngine"], dependencies=[Depends(require_prime_control_key)])

SECTIONS = {
    "rapport": "rapport_questions",
    "diagnostic": "diagnostic_questions",
    "numbers": "numbers_framing",
    "offer": "offer_framing",
    "objections": "objection_prompts",
    "closing": "closing_prompts",
}


def _session(db: Session, session_id: str, deal_id: int | None = None, *, lock: bool = False) -> CloserSession:
    session = db.get(CloserSession, session_id, with_for_update=lock)
    if session is None or (deal_id is not None and session.deal_id != deal_id):
        raise HTTPException(status_code=404, detail="Session not found or deal mismatch")
    return session


@router.post("/start", response_model=CloserSessionStartResponse)
def start_closing_session(payload: CloserSessionStartRequest, db: Session = Depends(get_db)):
    playbook = get_closing_playbook(payload.backend_deal_id, db)
    context = CloserSessionContext(
        closing_context=playbook["context"].model_dump(mode="json"),
        closing_playbook=playbook["script"],
    )
    session_id = str(uuid4())
    script = context.closing_playbook
    db.add(CloserSession(
        id=session_id, deal_id=payload.backend_deal_id, script=script,
        last_section="rapport", section_notes=[],
    ))
    db.commit()
    return CloserSessionStartResponse(
        session_id=session_id, backend_deal_id=payload.backend_deal_id,
        channel=payload.channel, role=payload.role, context=context,
        opening_line=script["opening"], first_prompts=script["rapport_questions"],
    )


@router.post("/next_block", response_model=CloserNextBlockResponse)
def get_next_block(payload: CloserNextBlockRequest, db: Session = Depends(get_db)):
    session = _session(db, payload.session_id, payload.backend_deal_id, lock=True)
    if payload.last_section != session.last_section:
        raise HTTPException(status_code=409, detail="Closer section has changed")
    if session.last_section == "done":
        raise HTTPException(status_code=409, detail="Closer script is complete")
    order = [*SECTIONS, "done"]
    next_section = order[order.index(session.last_section) + 1]
    value = session.script.get(SECTIONS.get(next_section), [])
    prompts = [value] if isinstance(value, str) else value
    notes = "Script completed. Review the owner-approved next steps." if next_section == "done" else None
    if payload.outcome:
        session.section_notes = [
            *session.section_notes, {"section": session.last_section, "outcome": payload.outcome},
        ]
    session.last_section = next_section
    db.commit()
    return CloserNextBlockResponse(
        session_id=payload.session_id, backend_deal_id=payload.backend_deal_id,
        next_section=next_section, prompts=prompts, notes=notes,
    )


@router.post("/feedback", response_model=CloserFeedbackResponse)
def record_closer_feedback(payload: CloserFeedbackRequest, db: Session = Depends(get_db)):
    session = _session(db, payload.session_id, payload.backend_deal_id, lock=True)
    session.feedback = payload.model_dump(mode="json", exclude={"session_id", "backend_deal_id"})
    db.commit()
    return CloserFeedbackResponse(
        session_id=payload.session_id, backend_deal_id=payload.backend_deal_id,
        disposition=payload.disposition, stored=True, notes="Operator feedback saved.",
    )


@router.get("/transcript/{session_id}")
def get_transcript_stub(session_id: str, db: Session = Depends(get_db)) -> dict:
    session = _session(db, session_id)
    return {
        "session_id": session.id, "backend_deal_id": session.deal_id,
        "status": "notes_only", "message": "Operator-entered notes and feedback.",
        "sections": session.section_notes, "feedback": session.feedback,
    }
