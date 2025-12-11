"""PACK 69: Code Compliance Service
Service layer for compliance check operations.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.code_compliance import ComplianceCheck


def run_compliance_check(
    db: Session,
    blueprint_id: int,
    region_code: str,
    violations: Optional[str],
    passed: str
) -> ComplianceCheck:
    """Run a compliance check on a blueprint."""
    chk = ComplianceCheck(
        blueprint_id=blueprint_id,
        region_code=region_code,
        violations=violations,
        passed=passed
    )
    db.add(chk)
    db.commit()
    db.refresh(chk)
    return chk


def list_checks(db: Session, blueprint_id: Optional[int] = None) -> list:
    """List compliance checks, optionally filtered by blueprint ID."""
    q = db.query(ComplianceCheck)
    if blueprint_id:
        q = q.filter(ComplianceCheck.blueprint_id == blueprint_id)
    return q.order_by(ComplianceCheck.id.desc()).all()
