from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.compliance_signal import ComplianceSignal
from app.schemas.compliance import ComplianceSignalCreate, ComplianceSignalOut

router = APIRouter()

@router.post("/", response_model=ComplianceSignalOut)
def create_compliance_signal(payload: ComplianceSignalCreate, db: Session = Depends(get_db)):
    obj = ComplianceSignal(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/", response_model=list[ComplianceSignalOut])
def list_compliance_signals(
    deal_id: int | None = None,
    severity: str | None = None,
    source: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ComplianceSignal)
    if deal_id is not None:
        query = query.filter(ComplianceSignal.deal_id == deal_id)
    if severity is not None:
        query = query.filter(ComplianceSignal.severity == severity)
    if source is not None:
        query = query.filter(ComplianceSignal.source == source)
    return query.all()
