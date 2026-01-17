"""
Pack 52: Negotiation & Psychology AI Enhancer - Service layer
"""
import json
from sqlalchemy.orm import Session
from app.neg_enhance.models import (
    ObjectionRow, RebuttalSnippet, PersonaKnob, SessionMetric, EscalationRule, NegReward
)

# Simple lexicons (placeholder heuristics)
POS_WORDS = {"great", "good", "perfect", "fair", "deal", "yes", "okay", "ok", "works"}
NEG_WORDS = {"no", "not", "never", "bad", "expensive", "ripoff", "hate", "waste"}
OBJECTION_HINTS = {
    "PRICE": ["too much", "too low", "price", "numbers don't work", "offer is low", "need more"],
    "TIMING": ["need time", "later", "not ready", "call back", "busy", "think about"],
    "TRUST": ["scam", "trust", "contract scary", "reviews", "who are you", "proof"],
    "PARTNER": ["spouse", "wife", "husband", "partner", "need approval"],
    "REPAIRS": ["repairs", "condition", "roof", "foundation", "too much work"],
}


def _sentiment(text: str) -> float:
    t = text.lower()
    score = sum(1 for w in POS_WORDS if w in t) - sum(1 for w in NEG_WORDS if w in t)
    score = max(-1.0, min(1.0, score / 5.0))
    return score


def _tone(text: str) -> str:
    t = text.lower()
    if "why" in t or "because" in t:
        return "analytical"
    if "please" in t or "thank" in t:
        return "empathetic"
    if any(x in t for x in ["now", "today", "must"]):
        return "assertive"
    return "calm"


def _intent(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["i will", "let's do", "send", "sign"]):
        return "decision"
    if any(k in t for k in ["can't", "don't", "won't", "no"]):
        return "objection"
    if any(k in t for k in ["later", "tomorrow", "next week", "think"]):
        return "stall"
    return "info"


def _objection_code(text: str):
    t = text.lower()
    for code, hints in OBJECTION_HINTS.items():
        if any(h in t for h in hints):
            return code
    return None


def analyze_text(db: Session, text: str, persona: str | None):
    s = _sentiment(text)
    tone = _tone(text)
    intent = _intent(text)
    obj = _objection_code(text)
    conf = 0.5 + 0.1 * abs(s) + (0.1 if obj else 0.0) + (0.1 if intent in ("decision", "objection") else 0.0)
    conf = max(0.0, min(1.0, conf))
    return {"sentiment": s, "tone": tone, "intent": intent, "confidence": conf, "objection_code": obj}


def suggest_rebuttal(db: Session, objection_code: str, persona: str | None, tone: str | None, max_len: int = 600):
    persona = persona or "consultant"
    q = db.query(RebuttalSnippet).filter(
        RebuttalSnippet.objection_code == objection_code,
        RebuttalSnippet.persona == persona,
    )
    if tone:
        q = q.filter(RebuttalSnippet.tone == tone)
    r = q.first() or db.query(RebuttalSnippet).filter(RebuttalSnippet.objection_code == objection_code).first()
    content = r.content if r else "Totally fair—can I understand what would make this a yes for you?"
    return {"content": content[:max_len], "confidence": 0.75 if r else 0.55}


def record_reward(db: Session, session_id: int, signal: str, weight: float, notes: str | None):
    row = NegReward(session_id=session_id, signal=signal, weight=weight, notes=notes)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def check_escalation(db: Session, conf_score: float):
    rule = db.query(EscalationRule).order_by(EscalationRule.threshold.asc()).first()
    if not rule:
        return {"should_escalate": conf_score >= 0.8, "action": "supervisor_notify", "payload": {"reason": "default"}}
    if conf_score >= rule.threshold:
        payload = json.loads(rule.payload_json) if rule.payload_json else {}
        return {"should_escalate": True, "action": rule.action, "payload": payload}
    return {"should_escalate": False, "action": None, "payload": None}
