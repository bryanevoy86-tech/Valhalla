"""
PACK CL16: Compliance Evidence Router
Prefix: /compliance/evidence
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.compliance_evidence import (
    ComplianceEvidenceCreate,
    ComplianceEvidenceOut,
    ComplianceEvidenceList,
)
from app.services.compliance_evidence import create_evidence, list_evidence

router = APIRouter(prefix="/compliance/evidence", tags=["Compliance", "EIA"])


@router.post("/", response_model=ComplianceEvidenceOut, status_code=201)
def create_compliance_evidence(payload: ComplianceEvidenceCreate, db: Session = Depends(get_db)):
    return create_evidence(db, payload)


@router.get("/", response_model=ComplianceEvidenceList)
def get_compliance_evidence(
    evidence_type: Optional[str] = Query(None),
    period: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    items = list_evidence(db, evidence_type=evidence_type, period=period, limit=limit)
    return ComplianceEvidenceList(total=len(items), items=[ComplianceEvidenceOut.model_validate(i) for i in items])
