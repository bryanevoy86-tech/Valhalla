"""
Pack 48: Heimdall Behavioral Core
Service layer for behavior scoring, script selection, and session management
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.behavior.models import BehaviorWeight, ScriptSnippet, NegotiationSession, BehaviorEvent
from app.behavior.schemas import BehaviorFeatures, ScoreOut, ScriptRequest, EventIn
from datetime import datetime
from typing import Optional


def score_features(db: Session, persona: str, features: BehaviorFeatures) -> ScoreOut:
    """
    Compute weighted behavioral score based on persona weights.
    Returns score, persona, and confidence (0.0-1.0).
    """
    weights = db.query(BehaviorWeight).filter_by(persona=persona).first()
    if not weights:
        # Default equal weighting
        raw_score = (
            features.trust + features.urgency + features.resistance +
            features.sentiment + features.authority
        ) / 5.0
        confidence = 0.5
    else:
        raw_score = (
            float(weights.trust_weight) * features.trust +
            float(weights.urgency_weight) * features.urgency +
            float(weights.resistance_weight) * features.resistance +
            float(weights.sentiment_weight) * features.sentiment +
            float(weights.authority_weight) * features.authority +
            float(weights.tone_weight) * (1.0 if features.tone == "positive" else 0.0)
        )
        total_weight = (
            float(weights.trust_weight) + float(weights.urgency_weight) +
            float(weights.resistance_weight) + float(weights.sentiment_weight) +
            float(weights.authority_weight) + float(weights.tone_weight)
        )
        raw_score = raw_score / max(total_weight, 0.01)
        confidence = 0.8  # Higher confidence with custom weights

    return ScoreOut(score=raw_score, persona=persona, confidence=confidence)


def pick_script(db: Session, req: ScriptRequest) -> Optional[ScriptSnippet]:
    """
    Select best script snippet matching persona, intent, tone, and confidence threshold.
    Returns None if no match found.
    """
    snippet = (
        db.query(ScriptSnippet)
        .filter(
            and_(
                ScriptSnippet.persona == req.persona,
                ScriptSnippet.intent == req.intent,
                ScriptSnippet.tone == req.tone,
                ScriptSnippet.confidence_threshold <= req.confidence
            )
        )
        .order_by(ScriptSnippet.confidence_threshold.desc())
        .first()
    )
    return snippet


def start_session(db: Session, session_id: str, persona: str, lead_id: Optional[int], deal_id: Optional[int]) -> NegotiationSession:
    """
    Start a new negotiation session.
    """
    sess = NegotiationSession(
        session_id=session_id,
        persona=persona,
        lead_id=lead_id,
        deal_id=deal_id
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


def add_event(db: Session, event_in: EventIn) -> BehaviorEvent:
    """
    Log a behavior event to a session.
    """
    evt = BehaviorEvent(
        session_id=event_in.session_id,
        event_type=event_in.event_type,
        speaker=event_in.speaker,
        text=event_in.text,
        trust_score=event_in.trust_score,
        urgency_score=event_in.urgency_score,
        resistance_score=event_in.resistance_score,
        sentiment_score=event_in.sentiment_score,
        authority_score=event_in.authority_score,
        tone=event_in.tone,
        intent=event_in.intent
    )
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return evt


def end_session(db: Session, session_id: str, outcome: str, summary: Optional[str]) -> Optional[NegotiationSession]:
    """
    End a negotiation session with outcome and summary.
    """
    sess = db.query(NegotiationSession).filter_by(session_id=session_id).first()
    if not sess:
        return None
    sess.ended_at = datetime.utcnow()
    sess.outcome = outcome
    sess.summary = summary
    db.commit()
    db.refresh(sess)
    return sess


def get_session(db: Session, session_id: str) -> Optional[NegotiationSession]:
    """
    Retrieve a negotiation session by session_id.
    """
    return db.query(NegotiationSession).filter_by(session_id=session_id).first()


def list_events(db: Session, session_id: str) -> list[BehaviorEvent]:
    """
    List all behavior events for a session.
    """
    return db.query(BehaviorEvent).filter_by(session_id=session_id).order_by(BehaviorEvent.timestamp).all()
