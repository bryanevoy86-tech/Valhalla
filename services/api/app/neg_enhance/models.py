"""
Pack 52: Negotiation & Psychology AI Enhancer - ORM models
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.db import Base


class ObjectionRow(Base):
    __tablename__ = "objection_catalog"
    id = Column(Integer, primary_key=True)
    code = Column(String(32), unique=True, nullable=False)
    pattern_regex = Column(Text, nullable=False)
    severity = Column(String(16), nullable=False)
    notes = Column(Text)


class RebuttalSnippet(Base):
    __tablename__ = "rebuttal_snippets"
    id = Column(Integer, primary_key=True)
    objection_code = Column(String(32), nullable=False)
    persona = Column(String(48), nullable=False)
    tone = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)


class PersonaKnob(Base):
    __tablename__ = "persona_knobs"
    id = Column(Integer, primary_key=True)
    persona = Column(String(48), unique=True, nullable=False)
    ask_softener_pct = Column(Float, nullable=False)
    mirror_ack_rate = Column(Float, nullable=False)
    probe_depth = Column(Integer, nullable=False)


class SessionMetric(Base):
    __tablename__ = "session_metrics"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("negotiation_sessions.id", ondelete="CASCADE"))
    turn_count = Column(Integer, nullable=False)
    last_tone = Column(String(32))
    avg_sentiment = Column(Float, nullable=False)
    conf_score = Column(Float, nullable=False)
    objection_last = Column(String(32))
    updated_at = Column(DateTime, server_default=func.now())


class EscalationRule(Base):
    __tablename__ = "escalation_rules"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    threshold = Column(Float, nullable=False)
    action = Column(String(64), nullable=False)
    payload_json = Column(Text)


class NegReward(Base):
    __tablename__ = "neg_rewards"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("negotiation_sessions.id", ondelete="CASCADE"))
    signal = Column(String(32), nullable=False)
    weight = Column(Float, nullable=False)
    notes = Column(Text)
