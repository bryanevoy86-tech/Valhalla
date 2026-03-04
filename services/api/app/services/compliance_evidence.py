"""
PACK CL16: Compliance Evidence Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.compliance_evidence import ComplianceEvidence
from app.schemas.compliance_evidence import ComplianceEvidenceCreate


def create_evidence(db: Session, payload: ComplianceEvidenceCreate) -> ComplianceEvidence:
    obj = ComplianceEvidence(
        evidence_id=payload.evidence_id,
        evidence_type=payload.evidence_type,
        period=payload.period,
        title=payload.title,
        notes=payload.notes,
        references=payload.references,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_evidence(
    db: Session,
    evidence_type: Optional[str] = None,
    period: Optional[str] = None,
    limit: int = 500,
) -> List[ComplianceEvidence]:
    q = db.query(ComplianceEvidence).order_by(ComplianceEvidence.id.desc())
    if evidence_type:
        q = q.filter(ComplianceEvidence.evidence_type == evidence_type)
    if period:
        q = q.filter(ComplianceEvidence.period == period)
    return q.limit(limit).all()
