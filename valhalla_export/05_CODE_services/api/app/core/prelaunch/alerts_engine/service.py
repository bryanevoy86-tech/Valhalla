"""PACK-CORE-PRELAUNCH-01: Alerts Engine - Service"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from . import models, schemas


def create_alert(db: Session, data: schemas.AlertCreate) -> models.Alert:
    alert = models.Alert(**data.dict())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def list_alerts(
    db: Session,
    level: Optional[models.AlertLevel] = None,
    domain: Optional[models.AlertDomain] = None,
    status: Optional[models.AlertStatus] = None,
    limit: int = 100,
) -> List[models.Alert]:
    q = db.query(models.Alert)
    if level:
        q = q.filter(models.Alert.level == level)
    if domain:
        q = q.filter(models.Alert.domain == domain)
    if status:
        q = q.filter(models.Alert.status == status)
    return q.order_by(models.Alert.created_at.desc()).limit(limit).all()


def get_alert(db: Session, alert_id: UUID) -> Optional[models.Alert]:
    return db.query(models.Alert).filter(models.Alert.id == alert_id).first()


def update_alert(
    db: Session, alert: models.Alert, data: schemas.AlertUpdate
) -> models.Alert:
    for field, value in data.dict(exclude_unset=True).items():
        setattr(alert, field, value)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert
