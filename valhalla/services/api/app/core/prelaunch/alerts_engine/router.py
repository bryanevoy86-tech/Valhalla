"""PACK-CORE-PRELAUNCH-01: Alerts Engine - Router"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db

from . import models, schemas, service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=List[schemas.AlertRead])
def list_alerts(
    level: Optional[models.AlertLevel] = None,
    domain: Optional[models.AlertDomain] = None,
    status_filter: Optional[models.AlertStatus] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return service.list_alerts(
        db=db, level=level, domain=domain, status=status_filter, limit=limit
    )


@router.post("/", response_model=schemas.AlertRead, status_code=status.HTTP_201_CREATED)
def create_alert(
    payload: schemas.AlertCreate,
    db: Session = Depends(get_db),
):
    return service.create_alert(db=db, data=payload)


@router.post("/{alert_id}/resolve", response_model=schemas.AlertRead)
def resolve_alert(alert_id: UUID, db: Session = Depends(get_db)):
    alert = service.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    updated = service.update_alert(
        db,
        alert,
        schemas.AlertUpdate(status=models.AlertStatus.RESOLVED),
    )
    return updated
