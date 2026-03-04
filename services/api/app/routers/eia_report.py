"""
PACK CL18: EIA Report Router
Prefix: /eia
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.compliance_evidence import ComplianceEvidenceOut
from app.schemas.eia_report import EIAReportGenerateIn
from app.services.eia_report import generate_monthly_report

router = APIRouter(prefix="/eia", tags=["EIA", "Reporting"])


@router.post("/monthly-report", response_model=ComplianceEvidenceOut, status_code=201)
def create_eia_monthly_report(payload: EIAReportGenerateIn, db: Session = Depends(get_db)):
    return generate_monthly_report(db, period=payload.period, title=payload.title, notes=payload.notes)
