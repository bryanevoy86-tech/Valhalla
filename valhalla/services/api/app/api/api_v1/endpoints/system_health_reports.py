from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.system_health_report import SystemHealthReport
from app.schemas.system_health_report import (
    SystemHealthReportCreate,
    SystemHealthReportOut,
)

router = APIRouter()


@router.post("/", response_model=SystemHealthReportOut)
def create_system_health_report(payload: SystemHealthReportCreate, db: Session = Depends(get_db)):
    data = payload.dict()
    if data.get("run_at") is None:
        data["run_at"] = datetime.utcnow()
    obj = SystemHealthReport(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[SystemHealthReportOut])
def list_system_health_reports(db: Session = Depends(get_db)):
    return db.query(SystemHealthReport).order_by(SystemHealthReport.run_at.desc()).all()
