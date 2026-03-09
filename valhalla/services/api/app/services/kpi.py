from __future__ import annotations

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import json

from app.models.kpi_event import KPIEvent


def emit_kpi(
    db: Session,
    domain: str,
    metric: str,
    success: bool | None = None,
    value: float | None = None,
    actor: str | None = None,
    correlation_id: str | None = None,
    detail: Dict[str, Any] | str | None = None,
) -> int:
    payload = None
    if isinstance(detail, dict):
        payload = json.dumps(detail)
    elif isinstance(detail, str):
        payload = detail

    evt = KPIEvent(
        domain=domain.strip().upper(),
        metric=metric.strip().lower(),
        success=success,
        value=value,
        actor=actor,
        correlation_id=correlation_id,
        detail=payload,
    )
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return evt.id
