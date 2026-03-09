from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.income_engine import IncomeEngine
from app.models.revenue_ledger import RevenueLedger
from app.models.trajectory_target import TrajectoryTarget

FUN_FUND_PCT = Decimal("0.10")
OPS_PCT = Decimal("0.00")  # keep 0 for now unless you explicitly want ops reserves

def _d(v: float | Decimal) -> Decimal:
    return v if isinstance(v, Decimal) else Decimal(str(v))

def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def month_start(d: date) -> date:
    return date(d.year, d.month, 1)

def upsert_engine(db: Session, payload: dict) -> IncomeEngine:
    row = db.query(IncomeEngine).filter(IncomeEngine.code == payload["code"]).first()
    if not row:
        row = IncomeEngine(**payload)
        db.add(row)
    else:
        for k, v in payload.items():
            setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row

def record_revenue(db: Session, *, engine_code: str, gross_amount: float, currency: str, as_of_date: date, source_ref: str | None):
    gross = _q(_d(gross_amount))
    fun = _q(gross * FUN_FUND_PCT)
    ops = _q(gross * OPS_PCT)
    reinvest = _q(gross - fun - ops)

    row = RevenueLedger(
        engine_code=engine_code,
        source_ref=source_ref,
        currency=currency,
        gross_amount=gross,
        fun_fund_amount=fun,
        reinvest_amount=reinvest,
        ops_reserve_amount=ops,
        as_of_date=as_of_date,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def upsert_target(db: Session, payload: dict) -> TrajectoryTarget:
    m0 = month_start(payload["month"])
    row = (
        db.query(TrajectoryTarget)
        .filter(TrajectoryTarget.engine_code == payload["engine_code"], TrajectoryTarget.month == m0)
        .first()
    )
    payload["month"] = m0
    if not row:
        row = TrajectoryTarget(**payload)
        db.add(row)
    else:
        for k, v in payload.items():
            setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row

def evaluate_month(db: Session, *, month: date, engine_code: str = "SYSTEM"):
    m0 = month_start(month)

    q = db.query(
        func.coalesce(func.sum(RevenueLedger.gross_amount), 0),
        func.coalesce(func.sum(RevenueLedger.fun_fund_amount), 0),
    ).filter(func.date_trunc("month", RevenueLedger.as_of_date) == m0)

    if engine_code != "SYSTEM":
        q = q.filter(RevenueLedger.engine_code == engine_code)

    gross, fun = q.first()
    actual_gross = float(gross)
    actual_fun = float(fun)

    target = (
        db.query(TrajectoryTarget)
        .filter(TrajectoryTarget.engine_code == engine_code, TrajectoryTarget.month == m0)
        .first()
    )
    target_gross = float(target.min_gross) if target else 0.0
    target_fun = float(target.min_fun_fund) if target else 0.0
    currency = target.currency if target else "USD"

    gross_delta = actual_gross - target_gross
    fun_delta = actual_fun - target_fun
    ok = gross_delta >= 0 and fun_delta >= 0

    if ok:
        severity = "OK"
    else:
        # Critical if you're >10% below the fun fund target
        severity = "CRITICAL" if (target_fun > 0 and fun_delta < -0.10 * target_fun) else "WARNING"

    return {
        "month": m0,
        "currency": currency,
        "actual_gross": actual_gross,
        "target_gross": target_gross,
        "gross_delta": gross_delta,
        "actual_fun_fund": actual_fun,
        "target_fun_fund": target_fun,
        "fun_fund_delta": fun_delta,
        "ok": ok,
        "severity": severity,
    }
