"""Telemetry Hooks (Integrity Ledger) router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.telemetry.service import TelemetryService
from app.telemetry.schemas import TelemetryIn, TelemetryOut, TelemetryQuery

router = APIRouter(prefix='/telemetry', tags=['telemetry'])


@router.post('', response_model=TelemetryOut)
async def post_event(body: TelemetryIn, db: Session = Depends(get_db)):
    return TelemetryService(db).write(body)


@router.get('', response_model=list[TelemetryOut])
async def list_events(
    event: str | None = None,
    level: str | None = None,
    actor: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    q = TelemetryQuery(event=event, level=level, actor=actor, limit=limit, offset=offset)
    return TelemetryService(db).list(q)
