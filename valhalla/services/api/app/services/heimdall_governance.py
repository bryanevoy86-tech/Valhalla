from __future__ import annotations

import json
from datetime import datetime, date
from typing import Dict, Any, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.heimdall_policy import HeimdallPolicy
from app.models.heimdall_scorecard import HeimdallScorecardDay
from app.models.heimdall_recommendation import HeimdallRecommendation
from app.models.heimdall_event import HeimdallEvent


def _utc_day() -> date:
    return datetime.utcnow().date()


def _log(db: Session, domain: str, event: str, ok: bool, confidence: float | None, rec_id: int | None,
         actor: str | None, correlation_id: str | None, detail: Dict[str, Any] | str | None):
    payload = None
    if isinstance(detail, dict):
        payload = json.dumps(detail)
    elif isinstance(detail, str):
        payload = detail
    evt = HeimdallEvent(
        domain=domain,
        event=event,
        ok=ok,
        confidence=confidence,
        recommendation_id=rec_id,
        actor=actor,
        correlation_id=correlation_id,
        detail=payload,
        created_at=datetime.utcnow(),
    )
    db.add(evt)
    db.commit()


def get_or_create_policy(db: Session, domain: str) -> HeimdallPolicy:
    domain = domain.strip().upper()
    p = db.query(HeimdallPolicy).filter(HeimdallPolicy.domain == domain).first()
    if p:
        return p

    # SAFEST default: prod use disabled until you explicitly enable.
    p = HeimdallPolicy(
        domain=domain,
        min_confidence_prod=0.90,
        min_sandbox_trials=50,
        min_sandbox_success_rate=0.80,
        prod_use_enabled=False,
        changed_by="system",
        reason="Auto-created policy (default prod_use_disabled for safety)",
        updated_at=datetime.utcnow(),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def get_or_create_scorecard(db: Session, domain: str) -> HeimdallScorecardDay:
    domain = domain.strip().upper()
    d = _utc_day()
    row = db.query(HeimdallScorecardDay).filter(HeimdallScorecardDay.day == d, HeimdallScorecardDay.domain == domain).first()
    if row:
        return row
    row = HeimdallScorecardDay(day=d, domain=domain, trials=0, successes=0, success_rate=0.0, avg_confidence=0.0)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def record_sandbox_trial(db: Session, domain: str, confidence: float, success: bool) -> HeimdallScorecardDay:
    """
    Called by sandbox runners to update daily performance.
    """
    row = get_or_create_scorecard(db, domain)
    row.trials += 1
    if success:
        row.successes += 1
    row.success_rate = (row.successes / row.trials) if row.trials > 0 else 0.0

    # Running average confidence
    prev_total = max(0, row.trials - 1)
    if prev_total == 0:
        row.avg_confidence = float(confidence)
    else:
        row.avg_confidence = ((row.avg_confidence * prev_total) + float(confidence)) / float(row.trials)

    row.updated_at = datetime.utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def evaluate_prod_gate(db: Session, domain: str, confidence: float) -> Tuple[bool, str, Dict[str, Any], Dict[str, Any]]:
    """
    Gate logic:
    - prod_use_enabled must be True
    - confidence must meet threshold
    - scorecard must meet min trials and min success rate
    """
    domain = domain.strip().upper()
    p = get_or_create_policy(db, domain)
    s = get_or_create_scorecard(db, domain)

    policy_snapshot = {
        "domain": p.domain,
        "prod_use_enabled": p.prod_use_enabled,
        "min_confidence_prod": p.min_confidence_prod,
        "min_sandbox_trials": p.min_sandbox_trials,
        "min_sandbox_success_rate": p.min_sandbox_success_rate,
    }
    score_snapshot = {
        "day": str(s.day),
        "trials": s.trials,
        "success_rate": s.success_rate,
        "avg_confidence": s.avg_confidence,
    }

    if not p.prod_use_enabled:
        return False, "prod_use_disabled", policy_snapshot, score_snapshot

    if float(confidence) < float(p.min_confidence_prod):
        return False, "confidence_below_threshold", policy_snapshot, score_snapshot

    if s.trials < p.min_sandbox_trials:
        return False, "insufficient_sandbox_trials", policy_snapshot, score_snapshot

    if float(s.success_rate) < float(p.min_sandbox_success_rate):
        return False, "sandbox_success_rate_below_threshold", policy_snapshot, score_snapshot

    return True, "gate_pass", policy_snapshot, score_snapshot


def create_recommendation(
    db: Session,
    domain: str,
    confidence: float,
    recommendation: Dict[str, Any],
    evidence: Optional[Dict[str, Any]],
    actor: Optional[str],
    correlation_id: Optional[str],
) -> HeimdallRecommendation:
    domain_u = domain.strip().upper()
    ok, reason, pol, score = evaluate_prod_gate(db, domain_u, confidence)

    rec = HeimdallRecommendation(
        domain=domain_u,
        confidence=float(confidence),
        recommendation_json=json.dumps(recommendation),
        evidence_json=json.dumps(evidence) if evidence else None,
        correlation_id=correlation_id,
        actor=actor,
        prod_eligible=bool(ok),
        gate_reason=reason,
        created_at=datetime.utcnow(),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    _log(db, domain_u, "RECOMMEND_CREATED", True, float(confidence), rec.id, actor, correlation_id, {"gate": reason})
    _log(db, domain_u, "PROD_GATE_PASS" if ok else "PROD_GATE_FAIL", ok, float(confidence), rec.id, actor, correlation_id,
         {"policy": pol, "scorecard": score})

    return rec


def assert_prod_eligible(db: Session, recommendation_id: int, actor: Optional[str], correlation_id: Optional[str]) -> HeimdallRecommendation:
    """
    Called right before PROD_EXEC actions that want to rely on a Heimdall recommendation.
    """
    rec = db.query(HeimdallRecommendation).filter(HeimdallRecommendation.id == recommendation_id).first()
    if not rec:
        _log(db, "UNKNOWN", "PROD_GATE_FAIL", False, None, recommendation_id, actor, correlation_id, {"error": "recommendation_not_found"})
        raise RuntimeError("Heimdall recommendation not found")

    if not rec.prod_eligible:
        _log(db, rec.domain, "PROD_GATE_FAIL", False, rec.confidence, rec.id, actor, correlation_id,
             {"error": "recommendation_not_prod_eligible", "gate_reason": rec.gate_reason})
        raise RuntimeError(f"Heimdall recommendation not eligible for production: {rec.gate_reason}")

    return rec
