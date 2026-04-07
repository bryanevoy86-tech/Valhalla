"""
Pack 48: Heimdall Behavioral Core
ORM models for behavior_weights, script_snippets, negotiation_sessions, behavior_events
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, func
from app.core.db import Base


class BehaviorWeight(Base):
    __tablename__ = "behavior_weights"

    id = Column(Integer, primary_key=True, index=True)
    persona = Column(String(64), nullable=False, unique=True)
    trust_weight = Column(Numeric(5, 2), nullable=False, server_default="1.0")
    urgency_weight = Column(Numeric(5, 2), nullable=False, server_default="1.0")
    resistance_weight = Column(Numeric(5, 2), nullable=False, server_default="1.0")
    sentiment_weight = Column(Numeric(5, 2), nullable=False, server_default="1.0")
    authority_weight = Column(Numeric(5, 2), nullable=False, server_default="1.0")
    tone_weight = Column(Numeric(5, 2), nullable=False, server_default="1.0")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class ScriptSnippet(Base):
    __tablename__ = "script_snippets"

    id = Column(Integer, primary_key=True, index=True)
    snippet_name = Column(String(128), nullable=False, unique=True)
    persona = Column(String(64), nullable=False, index=True)
    intent = Column(String(64), nullable=False, index=True)
    tone = Column(String(64), nullable=False)
    text = Column(Text, nullable=False)
    confidence_threshold = Column(Numeric(5, 2), nullable=False, server_default="0.5")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class NegotiationSession(Base):
    __tablename__ = "negotiation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), nullable=False, unique=True)
    persona = Column(String(64), nullable=False)
    lead_id = Column(Integer, nullable=True, index=True)
    deal_id = Column(Integer, nullable=True, index=True)
    started_at = Column(DateTime, nullable=False, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)
    outcome = Column(String(64), nullable=True)
    summary = Column(Text, nullable=True)


class BehaviorEvent(Base):
    __tablename__ = "behavior_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    speaker = Column(String(32), nullable=False)
    text = Column(Text, nullable=True)
    trust_score = Column(Numeric(5, 2), nullable=True)
    urgency_score = Column(Numeric(5, 2), nullable=True)
    resistance_score = Column(Numeric(5, 2), nullable=True)
    sentiment_score = Column(Numeric(5, 2), nullable=True)
    authority_score = Column(Numeric(5, 2), nullable=True)
    tone = Column(String(64), nullable=True)
    intent = Column(String(64), nullable=True)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
