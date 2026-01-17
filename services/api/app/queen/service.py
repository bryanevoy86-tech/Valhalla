"""
Pack 55: Queen's Hub + Fun Fund Vaults - Service layer
"""
import os
import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.queen.models import QueenProfile, QueenVault, QueenVaultTxn, QueenMonthCap

def _profile(db: Session) -> QueenProfile:
    q = db.query(QueenProfile).first()
    if q:
        return q
    cap2 = Decimal(str(os.getenv("QUEEN_FUN_CAP_PHASE2", "10000")))
    q = QueenProfile(
        name=os.getenv("QUEEN_NAME", "Queen"),
        currency=os.getenv("QUEEN_BASE_CURRENCY", "CAD"),
        phase=2,
        cap_month=cap2,
        tax_rate=float(os.getenv("QUEEN_TAX_WITHHOLD_RATE", "0.18"))
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q

def _vault(db: Session) -> QueenVault:
    v = db.query(QueenVault).first()
    if v:
        return v
    v = QueenVault(label="Main Fun Vault", balance=0, currency=os.getenv("QUEEN_BASE_CURRENCY", "CAD"))
    db.add(v)
    db.commit()
    db.refresh(v)
    return v

def _cap_row(db: Session, yyyymm: str, phase: int) -> QueenMonthCap:
    row = db.query(QueenMonthCap).filter(QueenMonthCap.yyyymm == yyyymm).first()
    if row:
        return row
    allowed = Decimal(str(os.getenv("QUEEN_FUN_CAP_PHASE2", "10000"))) if phase == 2 else Decimal(str(os.getenv("QUEEN_FUN_CAP_PHASE3", "25000")))
    row = QueenMonthCap(yyyymm=yyyymm, allowed=allowed, used=0, phase=phase)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def status(db: Session):
    q = _profile(db)
    v = _vault(db)
    now = datetime.date.today().strftime("%Y-%m")
    cap = _cap_row(db, now, q.phase)
    return {
        "queen": {"name": q.name, "currency": q.currency, "phase": q.phase, "cap_month": float(q.cap_month), "tax_rate": q.tax_rate},
        "vault": {"balance": float(v.balance), "currency": v.currency},
        "cap": {"yyyymm": cap.yyyymm, "allowed": float(cap.allowed), "used": float(cap.used), "remaining": float(Decimal(cap.allowed) - Decimal(cap.used))}
    }

def adjust_phase(db: Session, phase: int, cap_month: float | None, tax_rate: float | None):
    q = _profile(db)
    q.phase = phase
    if cap_month is not None:
        q.cap_month = Decimal(str(cap_month))
    if tax_rate is not None:
        q.tax_rate = tax_rate
    db.commit()
    db.refresh(q)
    # roll cap row
    now = datetime.date.today().strftime("%Y-%m")
    _cap_row(db, now, q.phase)
    return q

def inflow(db: Session, amount: float, category: str | None, note: str | None):
    """Process gross inflow → withhold tax → enforce cap → net to Queen; redirect excess."""
    q = _profile(db)
    v = _vault(db)
    yyyymm = datetime.date.today().strftime("%Y-%m")
    cap = _cap_row(db, yyyymm, q.phase)
    gross = Decimal(str(amount))
    tax = (Decimal(str(q.tax_rate)) * gross).quantize(Decimal("0.01"))
    net = gross - tax
    # cap math
    room = Decimal(cap.allowed) - Decimal(cap.used)
    to_vault = min(net, room)
    redirect = net - to_vault
    # apply
    if tax > 0:
        db.add(QueenVaultTxn(vault_id=v.id, kind="tax_withheld", amount=tax, category=category, note=note))
    if to_vault > 0:
        v.balance = Decimal(v.balance) + to_vault
        db.add(QueenVaultTxn(vault_id=v.id, kind="inflow", amount=to_vault, category=category, note=note))
        cap.used = Decimal(cap.used) + to_vault
    if redirect > 0:
        db.add(QueenVaultTxn(vault_id=v.id, kind="cap_redirect", amount=redirect, category="redirect", note="Over-cap redirected to main vault/owner"))
    db.commit()
    db.refresh(v)
    db.refresh(cap)
    return {"gross": float(gross), "tax": float(tax), "net": float(net), "to_vault": float(to_vault), "redirect": float(redirect)}

def spend(db: Session, amount: float, category: str, note: str | None):
    v = _vault(db)
    amt = Decimal(str(amount))
    if Decimal(v.balance) < amt:
        return False, "Insufficient vault balance"
    v.balance = Decimal(v.balance) - amt
    db.add(QueenVaultTxn(vault_id=v.id, kind="outflow", amount=amt, category=category, note=note))
    db.commit()
    db.refresh(v)
    return True, None
