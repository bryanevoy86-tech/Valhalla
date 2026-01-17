"""Resort router (Pack 58)"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.resort.schemas import *
from app.resort import service as svc

router = APIRouter(prefix="/resort", tags=["resort"])

@router.post("/project")
def create_project(body: ProjectIn, db: Session = Depends(get_db)):
    r = svc.create_project(db, body.model_dump()); return {"id": r.id}

@router.get("/project/{pid}")
def get_project(pid: int, db: Session = Depends(get_db)):
    s = svc.project_status(db, pid)
    if not s: raise HTTPException(404, "not found")
    return s

@router.post("/vault/inflow")
def inflow(body: VaultInflow, db: Session = Depends(get_db)):
    bal = svc.vault_inflow(db, body.project_id, body.amount, body.note)
    if bal is None: raise HTTPException(404, "project missing")
    return {"balance": bal}

@router.post("/vault/outflow")
def outflow(body: VaultOutflow, db: Session = Depends(get_db)):
    bal, err = svc.vault_outflow(db, body.project_id, body.amount, body.note)
    if err: raise HTTPException(400, err)
    return {"balance": bal}

@router.post("/milestone")
def add_milestone(body: MilestoneIn, db: Session = Depends(get_db)):
    r = svc.milestone_add(db, body.model_dump()); return {"id": r.id}

@router.patch("/milestone/{mid}")
def patch_milestone(mid: int, status: str, percent: float | None = None, db: Session = Depends(get_db)):
    r = svc.milestone_update(db, mid, status, percent)
    if not r: raise HTTPException(404, "not found")
    return {"ok": True}

@router.post("/quote")
def add_quote(body: QuoteIn, db: Session = Depends(get_db)):
    r = svc.quote_add(db, body.model_dump()); return {"id": r.id}

@router.post("/quote/{qid}/status")
def set_quote(qid: int, status: str, db: Session = Depends(get_db)):
    r = svc.quote_set_status(db, qid, status)
    if not r: raise HTTPException(404, "not found")
    return {"ok": True}

@router.post("/funding")
def add_funding(body: FundingIn, db: Session = Depends(get_db)):
    r = svc.funding_add(db, body.model_dump()); return {"id": r.id}

@router.post("/residency")
def create_residency(body: ResidencyIn, db: Session = Depends(get_db)):
    r = svc.residency_create(db, body.model_dump()); return {"id": r.id}

@router.post("/residency/step")
def add_step(body: StepIn, db: Session = Depends(get_db)):
    r = svc.residency_step_add(db, body.model_dump()); return {"id": r.id}

@router.get("/residency/{tid}/progress")
def residency_progress(tid: int, db: Session = Depends(get_db)):
    s = svc.residency_progress(db, tid)
    if not s: raise HTTPException(404, "not found")
    return s

@router.get("/digest", response_model=DigestOut)
def digest(db: Session = Depends(get_db)):
    return svc.weekly_digest(db)
