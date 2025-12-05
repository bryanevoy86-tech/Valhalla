# services/api/app/routers/closer_engine.py

from __future__ import annotations

import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.deal import Deal
from app.schemas.closer_engine import (
    CloserFeedbackRequest,
    CloserFeedbackResponse,
    CloserNextBlockRequest,
    CloserNextBlockResponse,
    CloserSessionContext,
    CloserSessionStartRequest,
    CloserSessionStartResponse,
    CloserTranscriptStub,
)

# We will call existing endpoints in-process using TestClient against app.main.app
from app.main import app as main_app

router = APIRouter(
    prefix="/closer",
    tags=["CloserEngine"],
)

# Simple in-memory session store (per process).
# In real production you'd use Redis or DB, but this is enough for Year 1.
CLOSER_SESSIONS: Dict[str, Dict[str, Any]] = {}

_client = TestClient(main_app)


def _fetch_closing_context(backend_deal_id: int) -> Dict[str, Any]:
    resp = _client.get(f"/flow/closing_context/{backend_deal_id}")
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to fetch closing_context for deal {backend_deal_id}: "
            f"{resp.status_code}",
        )
    return resp.json()


def _fetch_closing_playbook(backend_deal_id: int) -> Dict[str, Any]:
    resp = _client.get(f"/flow/closing_playbook/{backend_deal_id}")
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to fetch closing_playbook for deal {backend_deal_id}: "
            f"{resp.status_code}",
        )
    return resp.json()


def _determine_next_section(last_section: str) -> str:
    sequence = [
        "opening",
        "rapport",
        "diagnostic",
        "numbers",
        "offer",
        "objections",
        "closing",
    ]
    if last_section not in sequence:
        return "opening"
    idx = sequence.index(last_section)
    if idx + 1 >= len(sequence):
        return "done"
    return sequence[idx + 1]


@router.post(
    "/start",
    response_model=CloserSessionStartResponse,
    status_code=status.HTTP_200_OK,
    summary="Start a closing session for a deal",
    description=(
        "Bootstraps a closing session by pulling the closing context and "
        "closing playbook for a given backend_deal_id. Returns a session_id, "
        "opening line, and initial prompts."
    ),
)
def start_closing_session(
    payload: CloserSessionStartRequest,
    db: Session = Depends(get_db),
) -> CloserSessionStartResponse:
    # Ensure deal exists
    deal = db.query(Deal).filter(Deal.id == payload.backend_deal_id).first()
    if deal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with id {payload.backend_deal_id} not found.",
        )

    # Fetch context + playbook via existing flow endpoints
    ctx_raw = _fetch_closing_context(payload.backend_deal_id)
    pb_raw = _fetch_closing_playbook(payload.backend_deal_id)

    context = CloserSessionContext(
        closing_context=ctx_raw["context"]
        if "context" in pb_raw
        else ctx_raw,
        closing_playbook=pb_raw["script"],
    )

    session_id = str(uuid.uuid4())

    # Extract opening + rapport prompts
    script = context.closing_playbook
    opening_line = script.get("opening") or ctx_raw.get("suggested_opening", "")
    first_prompts: List[str] = []

    if "rapport_questions" in script:
        first_prompts.extend(script["rapport_questions"])

    # Store minimal session state in memory
    CLOSER_SESSIONS[session_id] = {
        "backend_deal_id": payload.backend_deal_id,
        "channel": payload.channel,
        "role": payload.role,
        "context": context,
        "script": script,
        "last_section": "opening",
    }

    return CloserSessionStartResponse(
        session_id=session_id,
        backend_deal_id=payload.backend_deal_id,
        channel=payload.channel,
        role=payload.role,
        context=context,
        opening_line=opening_line,
        first_prompts=first_prompts,
    )


@router.post(
    "/next_block",
    response_model=CloserNextBlockResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the next block of the closing script",
    description=(
        "Given a session_id, backend_deal_id and the section you just finished, "
        "returns the next section and its prompts. This is a simple, deterministic "
        "sequence; Heimdall can improvise on top."
    ),
)
def get_next_block(
    payload: CloserNextBlockRequest,
) -> CloserNextBlockResponse:
    session = CLOSER_SESSIONS.get(payload.session_id)
    if not session or session.get("backend_deal_id") != payload.backend_deal_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or deal mismatch.",
        )

    script: Dict[str, Any] = session["script"]
    next_section = _determine_next_section(payload.last_section)

    if next_section == "done":
        prompts: List[str] = [
            "You've worked through the script. Recap the key points and either "
            "lock in the agreement or set a clear follow-up."
        ]
        notes = "Script complete; closer/Heimdall should summarize and close."
    else:
        key_map = {
            "opening": "opening",
            "rapport": "rapport_questions",
            "diagnostic": "diagnostic_questions",
            "numbers": "numbers_framing",
            "offer": "offer_framing",
            "objections": "objection_prompts",
            "closing": "closing_prompts",
        }
        key = key_map[next_section]
        raw = script.get(key, [])
        if isinstance(raw, list):
            prompts = raw
        else:
            prompts = [str(raw)]
        notes = None

    session["last_section"] = next_section

    return CloserNextBlockResponse(
        session_id=payload.session_id,
        backend_deal_id=payload.backend_deal_id,
        next_section=next_section,
        prompts=prompts,
        notes=notes,
    )


@router.post(
    "/feedback",
    response_model=CloserFeedbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Record closing feedback for a session",
    description=(
        "Lightweight logging of call outcome. For now this is stored in memory; "
        "later it can be wired into a persistent call log."
    ),
)
def record_closer_feedback(
    payload: CloserFeedbackRequest,
) -> CloserFeedbackResponse:
    session = CLOSER_SESSIONS.get(payload.session_id)
    if not session or session.get("backend_deal_id") != payload.backend_deal_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or deal mismatch.",
        )

    # For now we just attach feedback to the in-memory session.
    session["feedback"] = {
        "disposition": payload.disposition,
        "reason": payload.reason,
        "next_steps": payload.next_steps,
    }

    notes = (
        "Feedback stored in memory only. For persistence, wire this into a "
        "call_log table in a future pack."
    )

    return CloserFeedbackResponse(
        session_id=payload.session_id,
        backend_deal_id=payload.backend_deal_id,
        disposition=payload.disposition,
        stored=True,
        notes=notes,
    )


@router.get(
    "/transcript/{session_id}",
    response_model=CloserTranscriptStub,
    status_code=status.HTTP_200_OK,
    summary="Stub transcript endpoint",
    description=(
        "Placeholder endpoint. Returns a stub payload explaining that full "
        "transcript storage is not implemented yet."
    ),
)
def get_transcript_stub(
    session_id: str,
) -> CloserTranscriptStub:
    session = CLOSER_SESSIONS.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    backend_deal_id = session.get("backend_deal_id", 0)

    return CloserTranscriptStub(
        session_id=session_id,
        backend_deal_id=backend_deal_id,
        status="stub",
        message=(
            "Full transcript capture is not yet implemented. This endpoint exists "
            "as a contract placeholder; integrate with call recording/notes in a "
            "future iteration."
        ),
    )
