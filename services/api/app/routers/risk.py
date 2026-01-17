from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.risk_policy import RiskPolicy
from app.models.risk_ledger import RiskLedgerDay
from app.schemas.risk import (
    RiskPolicyOut,
    RiskPolicyUpsertIn,
    RiskLedgerOut,
    RiskCheckIn,
    RiskCheckOut,
)
from app.services.risk_guard import reserve_exposure, settle_result

router = APIRouter(prefix="/governance/risk", tags=["Governance", "Risk"])


@router.get("/policies", response_model=list[RiskPolicyOut])
def list_policies(db: Session = Depends(get_db)):
    rows = db.query(RiskPolicy).order_by(RiskPolicy.engine.asc()).all()
    return rows


@router.post("/policies/upsert", response_model=RiskPolicyOut)
def upsert_policy(body: RiskPolicyUpsertIn, db: Session = Depends(get_db)):
    engine = body.engine.strip().upper()
    row = db.query(RiskPolicy).filter(RiskPolicy.engine == engine).first()
    if not row:
        row = RiskPolicy(engine=engine)
        db.add(row)

    row.max_daily_loss = float(body.max_daily_loss)
    row.max_daily_exposure = float(body.max_daily_exposure)
    row.max_open_risk = float(body.max_open_risk)
    row.max_actions_per_day = int(body.max_actions_per_day)
    row.enabled = bool(body.enabled)
    row.changed_by = body.changed_by
    row.reason = body.reason
    db.commit()
    db.refresh(row)
    return row


@router.get("/ledger/today", response_model=list[RiskLedgerOut])
def ledger_today(db: Session = Depends(get_db)):
    from datetime import datetime
    d = datetime.utcnow().date()
    rows = db.query(RiskLedgerDay).filter(RiskLedgerDay.day == d).order_by(RiskLedgerDay.engine.asc()).all()
    return rows


@router.post("/check-and-reserve", response_model=RiskCheckOut)
def check_and_reserve(body: RiskCheckIn, db: Session = Depends(get_db)):
    result = reserve_exposure(
        db=db,
        engine=body.engine,
        amount=body.amount,
        actor=body.actor,
        reason=body.reason,
        correlation_id=body.correlation_id,
        metadata=body.metadata,
    )
    p = result["policy"]
    l = result["ledger"]
    return RiskCheckOut(
        ok=bool(result["ok"]),
        engine=body.engine.strip().upper(),
        reserved=body.amount if result["ok"] else 0.0,
        message=result["message"],
        policy_snapshot={
            "engine": p.engine,
            "enabled": p.enabled,
            "max_daily_loss": p.max_daily_loss,
            "max_daily_exposure": p.max_daily_exposure,
            "max_open_risk": p.max_open_risk,
            "max_actions_per_day": p.max_actions_per_day,
        },
        ledger_snapshot={
            "day": str(l.day),
            "engine": l.engine,
            "exposure_used": l.exposure_used,
            "open_risk_reserved": l.open_risk_reserved,
            "realized_loss": l.realized_loss,
            "actions_count": l.actions_count,
        },
    )


@router.post("/settle")
def settle(
    engine: str,
    reserved_amount: float,
    realized_loss: float = 0.0,
    actor: str | None = None,
    reason: str | None = None,
    correlation_id: str | None = None,
    db: Session = Depends(get_db),
):
    return settle_result(
        db=db,
        engine=engine,
        reserved_amount=reserved_amount,
        realized_loss=realized_loss,
        actor=actor,
        reason=reason,
        correlation_id=correlation_id,
        metadata=None,
    )
