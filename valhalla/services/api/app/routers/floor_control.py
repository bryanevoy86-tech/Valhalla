from __future__ import annotations
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.floor_control import (
    EngineUpsertIn, RevenueEventIn, RevenueEventOut,
    TargetUpsertIn, TrajectoryStatusOut
)
from app.services.floor_control import upsert_engine, record_revenue, upsert_target, evaluate_month

router = APIRouter(prefix="/api/governance/floor", tags=["Governance", "Floor Control"])

@router.post("/engines/upsert")
def engines_upsert(body: EngineUpsertIn, db: Session = Depends(get_db)):
    return upsert_engine(db, body.model_dump())

@router.post("/revenue/record", response_model=RevenueEventOut)
def revenue_record(body: RevenueEventIn, db: Session = Depends(get_db)):
    row = record_revenue(
        db,
        engine_code=body.engine_code,
        gross_amount=body.gross_amount,
        currency=body.currency,
        as_of_date=body.as_of_date,
        source_ref=body.source_ref,
    )
    return RevenueEventOut(
        engine_code=row.engine_code,
        gross_amount=float(row.gross_amount),
        fun_fund_amount=float(row.fun_fund_amount),
        reinvest_amount=float(row.reinvest_amount),
        ops_reserve_amount=float(row.ops_reserve_amount),
        currency=row.currency,
        as_of_date=row.as_of_date,
    )

@router.post("/targets/upsert")
def targets_upsert(body: TargetUpsertIn, db: Session = Depends(get_db)):
    return upsert_target(db, body.model_dump())

@router.get("/trajectory/month", response_model=TrajectoryStatusOut)
def trajectory_month(
    month: date = Query(..., description="Any date in the month; normalized to first day."),
    engine_code: str = Query("SYSTEM"),
    db: Session = Depends(get_db),
):
    data = evaluate_month(db, month=month, engine_code=engine_code)
    return TrajectoryStatusOut(**data)
