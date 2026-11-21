from __future__ import annotations
from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.services.prime_business_execution import _check_legacy, _event, _json, require_owner_mandate_key
from app.models.treasury_reconciliation import StatementImport
from app.services.treasury_reconciliation import StatementFixture, append_statement, payload_for, statement_ready, summary
from app.services.wealth_scenario import WealthScenario, project_household_and_treasury
from app.schemas.floor_control import (
    EngineUpsertIn, RevenueEventIn, RevenueEventOut,
    TargetUpsertIn, TrajectoryStatusOut
)
from app.services.floor_control import upsert_engine, record_revenue, upsert_target, evaluate_month

router = APIRouter(prefix="/api/governance/floor", tags=["Governance", "Floor Control"],
                   dependencies=[Depends(require_prime_control_key)])
owner = [Depends(require_owner_mandate_key)]

@router.post("/engines/upsert", dependencies=owner)
def engines_upsert(body: EngineUpsertIn, db: Session = Depends(get_db)):
    return upsert_engine(db, body.model_dump())

@router.post("/revenue/record", response_model=RevenueEventOut, dependencies=owner)
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

@router.post("/targets/upsert", dependencies=owner)
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


@router.post("/wealth/scenarios", status_code=201, dependencies=owner)
def record_wealth_scenario(payload: WealthScenario, db: Session = Depends(get_db)):
    scope = payload.scope.model_dump()
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        raise HTTPException(503, "Wealth scenario storage unavailable")
    _check_legacy(db, **scope)
    params = payload.model_dump(mode="json")
    event_id = f"WEALTH-SCENARIO-{payload.scenario_id}"
    event_type = "WEALTH_SCENARIO_RECORDED"
    event = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=event_id, event_type=event_type))
    if event:
        recorded = _json(event.payload_json, {})
        recorded_sha = recorded.pop("sha256", None)
        if (event.legacy_instance_id != scope["legacy_instance_id"] or recorded.get("request") != params
                or recorded_sha != artifact_digest("wealth_scenario", event_id, recorded)):
            raise HTTPException(409, "Wealth scenario ID or integrity mismatch")
        return {**recorded, "sha256": recorded_sha}
    result = {"request": params, "result": project_household_and_treasury(payload)}
    result["sha256"] = artifact_digest("wealth_scenario", event_id, result)
    _event(db, event_id=event_id, legacy_instance_id=scope["legacy_instance_id"], event_type=event_type,
           message="Owner-private household and treasury scenario recorded", payload=result)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Wealth scenario ID already used") from None
    return result


@router.post("/treasury/statement-fixtures", status_code=201, dependencies=owner)
def import_statement(payload: StatementFixture, db: Session = Depends(get_db)):
    if not statement_ready(db):
        raise HTTPException(503, "Statement fixture schema unavailable")
    _check_legacy(db, **payload.scope.model_dump())
    try:
        result = append_statement(db, payload, date.today())
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Statement, account or transaction identity already exists") from None
    return result


@router.get("/treasury/statement-fixtures/{statement_id}", dependencies=owner)
def get_statement(statement_id: UUID, db: Session = Depends(get_db)):
    if not statement_ready(db):
        raise HTTPException(503, "Statement fixture schema unavailable")
    row = db.get(StatementImport, statement_id)
    if row is None:
        raise HTTPException(404, "Statement fixture not found")
    request = payload_for(row)
    _check_legacy(db, **request.scope.model_dump())
    return {**summary(request), "sha256": row.digest}


@router.get("/treasury/legacy-vault-audit", dependencies=owner)
def historical_vault_audit(db: Session = Depends(get_db)):
    """Exclude historically paper-tagged balances from the treasury evidence projection."""
    from app.finops.models import VaultBalance

    if not inspect(db.connection()).has_table(VaultBalance.__tablename__):
        raise HTTPException(503, "Historical vault evidence unavailable")
    rows = db.scalars(select(VaultBalance).where(VaultBalance.last_source == "fx_engine")
                      .order_by(VaultBalance.id).limit(100))
    quarantined = [{"vault_id": row.id, "vault_code": row.vault_code, "currency": row.currency,
                    "recorded_unreconciled_amount": str(row.balance), "source": row.last_source,
                    "basis": "SUSPECT_PAPER_FX_PROVENANCE"} for row in rows]
    return {"quarantined": quarantined, "actual_accessible_funds_minor": None,
            "basis": "READ_ONLY_PROVENANCE_AUDIT", "result_limit": 100}
