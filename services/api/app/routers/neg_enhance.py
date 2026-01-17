"""
Pack 52: Negotiation & Psychology AI Enhancer - API router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.neg_enhance.schemas import *
from app.neg_enhance import service as svc

router = APIRouter(prefix="/neg", tags=["negotiation"])


@router.post("/analyze", response_model=AnalyzeOut)
def analyze(body: AnalyzeReq, db: Session = Depends(get_db)):
    return svc.analyze_text(db, body.text, body.persona)


@router.post("/rebuttal", response_model=RebuttalOut)
def rebuttal(body: RebuttalReq, db: Session = Depends(get_db)):
    out = svc.suggest_rebuttal(db, body.objection_code, body.persona, body.tone)
    return out


@router.post("/reward")
def reward(body: RewardIn, db: Session = Depends(get_db)):
    r = svc.record_reward(db, body.session_id, body.signal, body.weight, body.notes)
    return {"id": r.id}


@router.post("/escalate/check", response_model=EscalateOut)
def escalate_check(body: EscalateCheckIn, db: Session = Depends(get_db)):
    return svc.check_escalation(db, body.conf_score)
