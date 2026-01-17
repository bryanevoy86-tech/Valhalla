"""King Hub router"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.king import service
from app.king.schemas import InflowIn, SpendIn, RuleSetIn, StatusOut

router = APIRouter(prefix="/king", tags=["king"])

@router.get("/status", response_model=StatusOut)
def king_status(db: Session = Depends(get_db)):
    return service.status(db)

@router.post("/rules")
def king_set_rules(rule_in: RuleSetIn, db: Session = Depends(get_db)):
    return service.set_rules(db, rule_in.model_dump())

@router.post("/inflow")
def king_inflow(inflow: InflowIn, db: Session = Depends(get_db)):
    return service.inflow(db, inflow.amount, inflow.note)

@router.post("/spend")
def king_spend(sp: SpendIn, db: Session = Depends(get_db)):
    ok, err = service.spend(db, sp.vault, sp.amount, sp.note)
    return {"ok": ok, "error": err}
