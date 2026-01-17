"""
Pack 48: Heimdall Behavioral Core
API endpoints for behavior scoring, script selection, and session management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.behavior import service
from app.behavior.schemas import (
    BehaviorFeatures, ScoreOut, ScriptRequest, ScriptOut,
    SessionStart, SessionOut, EventIn, EventOut
)
from typing import List

router = APIRouter(prefix="/behavior", tags=["behavior"])


@router.post("/score", response_model=ScoreOut)
def score_behavior(persona: str, features: BehaviorFeatures, db: Session = Depends(get_db)):
    """
    Compute weighted behavioral score for given persona and features.
    """
    return service.score_features(db, persona, features)


@router.post("/script", response_model=ScriptOut)
def get_script(req: ScriptRequest, db: Session = Depends(get_db)):
    """
    Select best script snippet matching persona, intent, tone, and confidence threshold.
    """
    snippet = service.pick_script(db, req)
    if not snippet:
        raise HTTPException(status_code=404, detail="No matching script snippet found")
    return snippet


@router.post("/session/start", response_model=SessionOut, status_code=201)
def start_negotiation(data: SessionStart, db: Session = Depends(get_db)):
    """
    Start a new negotiation session.
    """
    sess = service.start_session(db, data.session_id, data.persona, data.lead_id, data.deal_id)
    return sess


@router.get("/session/{session_id}", response_model=SessionOut)
def get_session(session_id: str, db: Session = Depends(get_db)):
    """
    Get negotiation session by session_id.
    """
    sess = service.get_session(db, session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    return sess


@router.post("/session/event", response_model=EventOut, status_code=201)
def log_event(event: EventIn, db: Session = Depends(get_db)):
    """
    Log a behavior event to a session.
    """
    return service.add_event(db, event)


@router.get("/session/{session_id}/events", response_model=List[EventOut])
def list_session_events(session_id: str, db: Session = Depends(get_db)):
    """
    List all behavior events for a session.
    """
    return service.list_events(db, session_id)


@router.post("/session/end", response_model=SessionOut)
def end_negotiation(session_id: str, outcome: str, summary: str = None, db: Session = Depends(get_db)):
    """
    End a negotiation session with outcome and summary.
    """
    sess = service.end_session(db, session_id, outcome, summary)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    return sess
