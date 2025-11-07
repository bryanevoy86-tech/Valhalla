"""
Pack 55: Queen's Hub + Fun Fund Vaults - Seed defaults
"""
import os
from decimal import Decimal
from sqlalchemy.orm import Session
from app.queen.models import QueenProfile, QueenVault, QueenMonthCap

def run(db: Session):
    q = db.query(QueenProfile).first()
    if not q:
        q = QueenProfile(
            name=os.getenv("QUEEN_NAME", "Lanna"),
            currency=os.getenv("QUEEN_BASE_CURRENCY", "CAD"),
            phase=2,
            cap_month=Decimal(str(os.getenv("QUEEN_FUN_CAP_PHASE2", "10000"))),
            tax_rate=float(os.getenv("QUEEN_TAX_WITHHOLD_RATE", "0.18"))
        )
        db.add(q)
        db.commit()
        db.refresh(q)
    v = db.query(QueenVault).first()
    if not v:
        v = QueenVault(label="Main Fun Vault", balance=0, currency=os.getenv("QUEEN_BASE_CURRENCY", "CAD"))
        db.add(v)
        db.commit()
    # Get current month in YYYY-MM format
    import datetime
    now = datetime.date.today().strftime("%Y-%m")
    if not db.query(QueenMonthCap).filter(QueenMonthCap.yyyymm == now).first():
        db.add(QueenMonthCap(
            yyyymm=now,
            allowed=Decimal(str(os.getenv("QUEEN_FUN_CAP_PHASE2", "10000"))),
            used=0,
            phase=2
        ))
        db.commit()
    print("✅ Pack 55: Queen's Hub seed loaded")
