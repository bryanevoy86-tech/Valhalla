"""
PACK CL19: Export Router
Prefix: /exports
Provides JSON exports for WeWeb downloads and compliance.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.compliance_evidence import ComplianceEvidenceList, ComplianceEvidenceOut
from app.services.compliance_evidence import list_evidence

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.get("/compliance/evidence", response_model=ComplianceEvidenceList)
def export_compliance_evidence(
    evidence_type: str | None = Query(None),
    period: str | None = Query(None),
    limit: int = Query(2000, ge=1, le=10000),
    db: Session = Depends(get_db),
):
    items = list_evidence(db, evidence_type=evidence_type, period=period, limit=limit)
    return ComplianceEvidenceList(total=len(items), items=[ComplianceEvidenceOut.model_validate(i) for i in items])
