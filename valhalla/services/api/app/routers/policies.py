from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.policies.schemas import (
    ClonePolicyIn,
    ClonePolicyOut,
    MirrorPolicyIn,
    MirrorPolicyOut,
    GateSnapshot,
    EvaluateResult,
)
from app.policies.models import ClonePolicy, MirrorPolicy, PolicyGateMetric
from app.policies.service import evaluate_clone, evaluate_mirror, log_event, touch_last_trigger

router = APIRouter(prefix="/policies", tags=["policies"])


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
    log_event(db, "clone", allow, reason, snap.model_dump())
    if not allow:
        return EvaluateResult(allow=False, reason=reason)
    # TODO: call orchestrator from Pack 42 to spin new Legacy
    touch_last_trigger(db, "clone")
    return EvaluateResult(allow=True, reason="Clone orchestration dispatched.")


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
    log_event(db, "mirror", allow, reason, snap.model_dump())
    if not allow:
        return EvaluateResult(allow=False, reason=reason)
    # TODO: dispatch mirror deployment (traffic split)
    touch_last_trigger(db, "mirror")
    return EvaluateResult(allow=True, reason="Mirror orchestration dispatched.")
