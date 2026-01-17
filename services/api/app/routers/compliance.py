from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.compliance.schemas import ComplianceCreate, ComplianceResponse
from app.compliance.service import create_compliance, list_records


router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.post("/", response_model=ComplianceResponse)
def add_compliance_record(payload: ComplianceCreate, db: Session = Depends(get_db)):
    return create_compliance(db, payload)


@router.get("/", response_model=List[ComplianceResponse])
def all_compliance_records(db: Session = Depends(get_db)):
    return list_records(db)
