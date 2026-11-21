from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.policies.schemas import (
    ClonePolicyIn,
    ClonePolicyOut,
    MirrorPolicyIn,
    MirrorPolicyOut,
    GateSnapshot,
    EvaluateResult,
)
from app.policies.models import ClonePolicy, MirrorPolicy, PolicyGateMetric
from app.policies.service import evaluate_clone, evaluate_mirror, log_event

router = APIRouter(prefix="/policies", tags=["policies"], dependencies=[Depends(require_prime_control_key)])


@router.get("/clone", response_model=ClonePolicyOut)
def get_clone_policy(db: Session = Depends(get_db)):
    p = db.query(ClonePolicy).first()
    if not p:
        raise HTTPException(404, "No clone policy")
    return p


@router.put("/clone", response_model=ClonePolicyOut)
def put_clone_policy(body: ClonePolicyIn, db: Session = Depends(get_db)):
    p = db.query(ClonePolicy).first()
    if not p:
        p = ClonePolicy(**body.model_dump())
        db.add(p)
    else:
        for k, v in body.model_dump().items():
            setattr(p, k, v)
    db.commit(); db.refresh(p)
    return p


@router.post("/clone/evaluate", response_model=EvaluateResult)
def post_clone_evaluate(snap: GateSnapshot, db: Session = Depends(get_db)):
    db.add(PolicyGateMetric(**snap.model_dump())); db.commit()
    allow, reason = evaluate_clone(db, snap.model_dump())
    log_event(db, "clone", allow, reason, snap.model_dump())
    return EvaluateResult(allow=allow, reason=reason)


@router.post("/clone/trigger", response_model=EvaluateResult)
def post_clone_trigger(snap: GateSnapshot, db: Session = Depends(get_db)):
    allow, reason = evaluate_clone(db, snap.model_dump())
    if allow:
        reason = "Clone orchestration is unavailable. Policy thresholds passed, but no dispatcher is configured."
    log_event(db, "clone", False, reason, snap.model_dump())
    return EvaluateResult(allow=False, reason=reason)


@router.get("/mirror", response_model=MirrorPolicyOut)
def get_mirror_policy(db: Session = Depends(get_db)):
    p = db.query(MirrorPolicy).first()
    if not p:
        raise HTTPException(404, "No mirror policy")
    return p


@router.put("/mirror", response_model=MirrorPolicyOut)
def put_mirror_policy(body: MirrorPolicyIn, db: Session = Depends(get_db)):
    p = db.query(MirrorPolicy).first()
    if not p:
        p = MirrorPolicy(**body.model_dump())
        db.add(p)
    else:
        for k, v in body.model_dump().items():
            setattr(p, k, v)
    db.commit(); db.refresh(p)
    return p


@router.post("/mirror/evaluate", response_model=EvaluateResult)
def post_mirror_evaluate(snap: GateSnapshot, db: Session = Depends(get_db)):
    db.add(PolicyGateMetric(**snap.model_dump())); db.commit()
    allow, reason = evaluate_mirror(db, snap.model_dump())
    log_event(db, "mirror", allow, reason, snap.model_dump())
    return EvaluateResult(allow=allow, reason=reason)


@router.post("/mirror/trigger", response_model=EvaluateResult)
def post_mirror_trigger(snap: GateSnapshot, db: Session = Depends(get_db)):
    allow, reason = evaluate_mirror(db, snap.model_dump())
    if allow:
        reason = "Mirror orchestration is unavailable. Policy thresholds passed, but no dispatcher is configured."
    log_event(db, "mirror", False, reason, snap.model_dump())
    return EvaluateResult(allow=False, reason=reason)
