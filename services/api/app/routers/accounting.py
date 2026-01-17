"""
Pack 50: Full Accounting Suite - API router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.accounting.schemas import *
from app.accounting import service as svc
from app.accounting.models import Account, Period

router = APIRouter(prefix="/accounting", tags=["accounting"])


@router.post("/accounts", response_model=AccountOut)
def create_account(body: AccountIn, db: Session = Depends(get_db)):
    a = svc.ensure_account(db, body.model_dump())
    return AccountOut.model_validate(a)


@router.get("/accounts", response_model=list[AccountOut])
def list_accounts(db: Session = Depends(get_db)):
    rows = db.query(Account).order_by(Account.code.asc()).all()
    return [AccountOut.model_validate(r) for r in rows]


@router.post("/journal/post", response_model=PostResult)
def post_journal(body: JournalEntryIn, db: Session = Depends(get_db)):
    try:
        entry_id, balanced = svc.post_entry(db, body.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"entry_id": entry_id, "balanced": balanced}


@router.post("/periods")
def create_period(body: PeriodIn, db: Session = Depends(get_db)):
    p = Period(**body.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "label": p.label}


@router.post("/report/pnl", response_model=PnLReport)
def report_pnl(req: ReportReq, db: Session = Depends(get_db)):
    return svc.pnl(db, req.model_dump())


@router.post("/report/tb", response_model=TBReport)
def report_tb(req: ReportReq, db: Session = Depends(get_db)):
    return svc.trial_balance(db, req.model_dump())


@router.post("/report/tax", response_model=TaxReport)
def report_tax(req: ReportReq, db: Session = Depends(get_db)):
    return svc.tax_report(db, req.model_dump())


@router.post("/cra/summary", response_model=CRASummary)
def cra_summary(req: ReportReq, db: Session = Depends(get_db)):
    tax = svc.tax_report(db, req.model_dump())
    period_label = req.period_label or f"{req.start_date}:{req.end_date}"
    return svc.cra_bot_summary(db, period_label, tax)
