from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from ..core.db import get_db
from ..models.intake import CapitalIntake
from ..schemas.intake import CapitalIn, CapitalOut

router = APIRouter(prefix="/capital", tags=["capital"])

@router.post("/intake", response_model=CapitalOut)
def record_intake(payload: CapitalIn, db: Session = Depends(get_db)):
    # Guardrails: non-negative amounts
    if Decimal(payload.amount) < 0:
        raise HTTPException(status_code=400, detail="Amount must be >= 0")

    rec = CapitalIntake(
        source=payload.source,
        amount=payload.amount,
        currency=payload.currency,
        note=payload.note,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

@router.get("/intake", response_model=List[CapitalOut])
def list_intake(db: Session = Depends(get_db)):
    return db.query(CapitalIntake).order_by(CapitalIntake.id.desc()).all()
