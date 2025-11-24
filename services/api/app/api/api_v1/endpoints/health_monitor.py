from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.system_health import SystemHealth
from app.schemas.health import (
    SystemHealthCreate,
    SystemHealthUpdate,
    SystemHealthOut,
)

router = APIRouter()


@router.post("/", response_model=SystemHealthOut)
def register_service(payload: SystemHealthCreate, db: Session = Depends(get_db)):
    existing = db.query(SystemHealth).filter(SystemHealth.service_name == payload.service_name).first()
    if existing:
        existing.status = payload.status or existing.status
        existing.notes = payload.notes or existing.notes
        existing.last_heartbeat = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    obj = SystemHealth(
        service_name=payload.service_name,
        status=payload.status,
        notes=payload.notes,
        last_heartbeat=datetime.utcnow(),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[SystemHealthOut])
def list_services(db: Session = Depends(get_db)):
    return db.query(SystemHealth).all()


@router.put("/{service_id}", response_model=SystemHealthOut)
def update_service(service_id: int, payload: SystemHealthUpdate, db: Session = Depends(get_db)):
    obj = db.query(SystemHealth).get(service_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    if payload.last_heartbeat is None:
        obj.last_heartbeat = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return obj
