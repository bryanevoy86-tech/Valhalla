"""Private Prime integrity inspection and audit capture."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.services.system_self_check import run_system_self_check

router = APIRouter(
    prefix="/api/system", tags=["system-integrity"],
    dependencies=[Depends(require_prime_control_key)],
)


def _inspect(db: Session, *, record_alerts: bool) -> dict:
    try:
        return run_system_self_check(db, record_alerts=record_alerts)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Integrity evidence unavailable") from None


@router.get("/self-check")
def inspect_integrity(db: Session = Depends(get_db)) -> dict:
    return _inspect(db, record_alerts=False)


@router.post("/self-check")
def record_integrity_check(db: Session = Depends(get_db)) -> dict:
    return _inspect(db, record_alerts=True)
