from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.heimdall_policy import HeimdallPolicy
from app.models.heimdall_scorecard import HeimdallScorecardDay
from app.schemas.heimdall import (
    HeimdallPolicyOut,
    HeimdallPolicyUpsertIn,
    HeimdallScorecardOut,
    HeimdallRecommendIn,
    HeimdallRecommendOut,
)
from app.services.heimdall_governance import get_or_create_policy, create_recommendation, record_sandbox_trial

router = APIRouter(prefix="/governance/heimdall", tags=["Governance", "Heimdall"])


@router.get("/policies", response_model=list[HeimdallPolicyOut])
def list_policies(db: Session = Depends(get_db)):
    return db.query(HeimdallPolicy).order_by(HeimdallPolicy.domain.asc()).all()


@router.post("/policies/upsert", response_model=HeimdallPolicyOut)
def upsert_policy(body: HeimdallPolicyUpsertIn, db: Session = Depends(get_db)):
    domain = body.domain.strip().upper()
    row = db.query(HeimdallPolicy).filter(HeimdallPolicy.domain == domain).first()
    if not row:
        row = get_or_create_policy(db, domain)
    row.min_confidence_prod = float(body.min_confidence_prod)
    row.min_sandbox_trials = int(body.min_sandbox_trials)
    row.min_sandbox_success_rate = float(body.min_sandbox_success_rate)
    row.prod_use_enabled = bool(body.prod_use_enabled)
    row.changed_by = body.changed_by
    row.reason = body.reason
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/scorecard/today", response_model=list[HeimdallScorecardOut])
def scorecard_today(db: Session = Depends(get_db)):
    from datetime import datetime
    d = datetime.utcnow().date()
    return db.query(HeimdallScorecardDay).filter(HeimdallScorecardDay.day == d).order_by(HeimdallScorecardDay.domain.asc()).all()


@router.post("/sandbox/trial", response_model=HeimdallScorecardOut)
def post_sandbox_trial(domain: str, confidence: float, success: bool, db: Session = Depends(get_db)):
    return record_sandbox_trial(db, domain=domain, confidence=confidence, success=success)


@router.post("/recommend", response_model=HeimdallRecommendOut)
def recommend(body: HeimdallRecommendIn, db: Session = Depends(get_db)):
    rec = create_recommendation(
        db=db,
        domain=body.domain,
        confidence=body.confidence,
        recommendation=body.recommendation,
        evidence=body.evidence,
        actor=body.actor,
        correlation_id=body.correlation_id,
    )
    return rec
