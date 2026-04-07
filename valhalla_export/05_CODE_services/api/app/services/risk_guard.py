from __future__ import annotations

import json
from datetime import datetime, date
from typing import Optional, Dict, Any, Tuple

from sqlalchemy.orm import Session

from app.models.risk_policy import RiskPolicy
from app.models.risk_ledger import RiskLedgerDay
from app.models.risk_event import RiskEvent


GLOBAL_ENGINE = "GLOBAL"


def _utc_day() -> date:
    return datetime.utcnow().date()


def _get_policy(db: Session, engine: str) -> RiskPolicy:
    p = db.query(RiskPolicy).filter(RiskPolicy.engine == engine).first()
    if p:
        return p
    # If missing, create a disabled policy by default (safer than assuming unlimited).
    p = RiskPolicy(
        engine=engine,
        enabled=False,
        max_daily_loss=0.0,
        max_daily_exposure=0.0,
        max_open_risk=0.0,
        max_actions_per_day=0,
        changed_by="system",
        reason="Auto-created missing policy (default disabled for safety)",
        updated_at=datetime.utcnow(),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _get_or_create_ledger(db: Session, engine: str) -> RiskLedgerDay:
    d = _utc_day()
    row = db.query(RiskLedgerDay).filter(RiskLedgerDay.day == d, RiskLedgerDay.engine == engine).first()
    if row:
        return row
    row = RiskLedgerDay(day=d, engine=engine, exposure_used=0.0, open_risk_reserved=0.0, realized_loss=0.0, actions_count=0)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _log_event(
    db: Session,
    engine: str,
    action: str,
    amount: float,
    ok: bool,
    reason: Optional[str],
    actor: Optional[str],
    correlation_id: Optional[str],
    metadata: Optional[Dict[str, Any]],
) -> None:
    evt = RiskEvent(
        engine=engine,
        action=action,
        amount=float(amount),
        ok=bool(ok),
        reason=reason,
        actor=actor,
        correlation_id=correlation_id,
        metadata_json=json.dumps(metadata) if metadata else None,
        created_at=datetime.utcnow(),
    )
    db.add(evt)
    db.commit()


def _would_exceed(policy: RiskPolicy, ledger: RiskLedgerDay, reserve_amount: float) -> Tuple[bool, str]:
    if not policy.enabled:
        return True, "Policy disabled"

    if policy.max_actions_per_day > 0 and (ledger.actions_count + 1) > policy.max_actions_per_day:
        return True, f"Actions/day cap exceeded ({ledger.actions_count + 1} > {policy.max_actions_per_day})"

    if policy.max_daily_exposure > 0 and (ledger.exposure_used + reserve_amount) > policy.max_daily_exposure:
        return True, f"Daily exposure cap exceeded ({ledger.exposure_used + reserve_amount} > {policy.max_daily_exposure})"

    if policy.max_open_risk > 0 and (ledger.open_risk_reserved + reserve_amount) > policy.max_open_risk:
        return True, f"Open risk cap exceeded ({ledger.open_risk_reserved + reserve_amount} > {policy.max_open_risk})"

    # max_daily_loss enforces via settle() (realized loss), but we can pre-block if already blown
    if policy.max_daily_loss > 0 and ledger.realized_loss >= policy.max_daily_loss:
        return True, f"Daily loss cap already reached ({ledger.realized_loss} >= {policy.max_daily_loss})"

    return False, "OK"


def reserve_exposure(
    db: Session,
    engine: str,
    amount: float,
    actor: Optional[str] = None,
    reason: Optional[str] = None,
    correlation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Reserve exposure before executing an action.
    This prevents concurrency slips (two actions consuming the same headroom).
    Enforces BOTH GLOBAL and engine policies.
    """
    engine = engine.strip().upper()
    d = _utc_day()

    # policies & ledgers
    p_global = _get_policy(db, GLOBAL_ENGINE)
    p_engine = _get_policy(db, engine)

    l_global = _get_or_create_ledger(db, GLOBAL_ENGINE)
    l_engine = _get_or_create_ledger(db, engine)

    # check global then engine
    exceed, msg = _would_exceed(p_global, l_global, amount)
    if exceed:
        _log_event(db, engine, "DENY", amount, False, f"GLOBAL: {msg}", actor, correlation_id, metadata)
        return {"ok": False, "message": f"GLOBAL hard stop: {msg}", "policy": p_global, "ledger": l_global}

    exceed, msg = _would_exceed(p_engine, l_engine, amount)
    if exceed:
        _log_event(db, engine, "DENY", amount, False, f"{engine}: {msg}", actor, correlation_id, metadata)
        return {"ok": False, "message": f"{engine} hard stop: {msg}", "policy": p_engine, "ledger": l_engine}

    # reserve (apply to both global + engine)
    l_global.exposure_used += amount
    l_global.open_risk_reserved += amount
    l_global.actions_count += 1
    l_global.updated_at = datetime.utcnow()

    l_engine.exposure_used += amount
    l_engine.open_risk_reserved += amount
    l_engine.actions_count += 1
    l_engine.updated_at = datetime.utcnow()

    db.add(l_global)
    db.add(l_engine)
    db.commit()

    _log_event(db, engine, "RESERVE", amount, True, reason, actor, correlation_id, metadata)

    return {"ok": True, "message": "Reserved", "policy": p_engine, "ledger": l_engine, "day": d}


def settle_result(
    db: Session,
    engine: str,
    reserved_amount: float,
    realized_loss: float = 0.0,
    actor: Optional[str] = None,
    reason: Optional[str] = None,
    correlation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Settle an action outcome:
    - Releases open_risk_reserved
    - Applies realized loss (if any)
    Enforces max_daily_loss by potentially keeping policy enabled but triggering future denies.
    """
    engine = engine.strip().upper()

    p_global = _get_policy(db, GLOBAL_ENGINE)
    p_engine = _get_policy(db, engine)

    l_global = _get_or_create_ledger(db, GLOBAL_ENGINE)
    l_engine = _get_or_create_ledger(db, engine)

    reserved_amount = max(0.0, float(reserved_amount))
    realized_loss = max(0.0, float(realized_loss))

    # release reserves
    l_global.open_risk_reserved = max(0.0, l_global.open_risk_reserved - reserved_amount)
    l_engine.open_risk_reserved = max(0.0, l_engine.open_risk_reserved - reserved_amount)

    # apply loss
    l_global.realized_loss += realized_loss
    l_engine.realized_loss += realized_loss

    l_global.updated_at = datetime.utcnow()
    l_engine.updated_at = datetime.utcnow()

    db.add(l_global)
    db.add(l_engine)
    db.commit()

    _log_event(db, engine, "SETTLE", realized_loss, True, reason, actor, correlation_id, metadata)

    # if loss caps breached, guard will auto-deny future actions today
    flags = []
    if p_global.max_daily_loss > 0 and l_global.realized_loss >= p_global.max_daily_loss:
        flags.append("GLOBAL daily loss cap reached")
    if p_engine.max_daily_loss > 0 and l_engine.realized_loss >= p_engine.max_daily_loss:
        flags.append(f"{engine} daily loss cap reached")

    return {"ok": True, "message": "Settled", "flags": flags, "ledger_engine": l_engine, "ledger_global": l_global}
