"""Risk Guard helper functions for drop-in integration.

This is the key "drop-in" you can call from any engine/router with two lines.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.services.risk_guard import reserve_exposure, settle_result


def risk_reserve_or_raise(
    db: Session,
    engine: str,
    amount: float,
    actor: Optional[str] = None,
    reason: Optional[str] = None,
    correlation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> float:
    """
    Reserve exposure or raise an exception upstream.
    Returns reserved amount (same as requested) if ok.
    """
    res = reserve_exposure(
        db=db,
        engine=engine,
        amount=amount,
        actor=actor,
        reason=reason,
        correlation_id=correlation_id,
        metadata=metadata,
    )
    if not res["ok"]:
        raise RuntimeError(res["message"])
    return float(amount)


def risk_settle(
    db: Session,
    engine: str,
    reserved_amount: float,
    realized_loss: float = 0.0,
    actor: Optional[str] = None,
    reason: Optional[str] = None,
    correlation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    settle_result(
        db=db,
        engine=engine,
        reserved_amount=reserved_amount,
        realized_loss=realized_loss,
        actor=actor,
        reason=reason,
        correlation_id=correlation_id,
        metadata=metadata,
    )
