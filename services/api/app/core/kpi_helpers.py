from __future__ import annotations

from contextlib import contextmanager
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.services.kpi import emit_kpi


def kpi_success(db: Session, domain: str, metric: str, actor: str | None = None, correlation_id: str | None = None, detail: Dict[str, Any] | None = None):
    emit_kpi(db, domain=domain, metric=metric, success=True, actor=actor, correlation_id=correlation_id, detail=detail)


def kpi_fail(db: Session, domain: str, metric: str, actor: str | None = None, correlation_id: str | None = None, detail: Dict[str, Any] | None = None):
    emit_kpi(db, domain=domain, metric=metric, success=False, actor=actor, correlation_id=correlation_id, detail=detail)


def kpi_value(db: Session, domain: str, metric: str, value: float, actor: str | None = None, correlation_id: str | None = None, detail: Dict[str, Any] | None = None):
    emit_kpi(db, domain=domain, metric=metric, value=float(value), actor=actor, correlation_id=correlation_id, detail=detail)


@contextmanager
def kpi_timed_step(db: Session, domain: str, metric: str, actor: Optional[str] = None, correlation_id: Optional[str] = None, detail: Optional[Dict[str, Any]] = None):
    """
    Use when you want an automatic success/fail KPI for a code block.
    """
    try:
        yield
        kpi_success(db, domain, metric, actor=actor, correlation_id=correlation_id, detail=detail)
    except Exception as e:
        kpi_fail(db, domain, metric, actor=actor, correlation_id=correlation_id, detail={**(detail or {}), "error": str(e)})
        raise
