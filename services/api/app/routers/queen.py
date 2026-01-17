"""
Pack 55: Queen's Hub + Fun Fund Vaults - API router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.queen.schemas import *
from app.queen import service as svc

router = APIRouter(prefix="/queen", tags=["queen"])

@router.get("/status")
def get_status(db: Session = Depends(get_db)):
    return svc.status(db)

@router.post("/phase", response_model=QueenOut)
def set_phase(body: AdjustPhaseIn, db: Session = Depends(get_db)):
    q = svc.adjust_phase(db, body.phase, body.cap_month, body.tax_rate)
    return q

@router.post("/inflow")
def add_inflow(body: InflowIn, db: Session = Depends(get_db)):
    return svc.inflow(db, body.amount, body.category, body.note)

@router.post("/spend")
def do_spend(body: SpendIn, db: Session = Depends(get_db)):
    ok, err = svc.spend(db, body.amount, body.category, body.note)
    if not ok:
        raise HTTPException(400, err or "insufficient")
    return {"ok": True}

@router.get("/vault", response_model=VaultOut)
def vault(db: Session = Depends(get_db)):
    s = svc.status(db)
    v = s["vault"]
    return {"balance": v["balance"], "currency": v["currency"]}

@router.get("/cap", response_model=CapStatus)
def cap_status(db: Session = Depends(get_db)):
    s = svc.status(db)
    c = s["cap"]
    return {"yyyymm": c["yyyymm"], "allowed": c["allowed"], "used": c["used"], "remaining": c["remaining"]}
