"""
PACK AN: Integrity Monitor Service
"""

from typing import List
from sqlalchemy.orm import Session

from app.schemas.integrity_monitor import IntegrityIssue, IntegrityReport
from app.models.wholesale import WholesalePipeline
from app.models.pro_retainer import Retainer
from app.models.contracts import Contract


def check_wholesale_integrity(db: Session) -> List[IntegrityIssue]:
    issues = []
    rows = db.query(WholesalePipeline).all()

    for r in rows:
        # Example: deal under contract but missing assigned dispo
        if r.stage == "under_contract" and not r.dispo_assigned:
            issues.append(
                IntegrityIssue(
                    category="pipeline_mismatch",
                    entity_type="wholesale_pipeline",
                    entity_id=r.id,
                    message="Under contract but no dispo assignment",
                )
            )
    return issues


def check_retainer_integrity(db: Session) -> List[IntegrityIssue]:
    issues = []
    rows = db.query(Retainer).all()

    for r in rows:
        if r.is_active and r.expiration_date and r.expiration_date < r.created_at:
            issues.append(
                IntegrityIssue(
                    category="retainer_invalid",
                    entity_type="professional_retainer",
                    entity_id=r.id,
                    message="Retainer expiration date precedes creation date",
                )
            )
    return issues


def check_contract_integrity(db: Session) -> List[IntegrityIssue]:
    issues = []
    rows = db.query(Contract).all()

    for c in rows:
        if not c.document_url:
            issues.append(
                IntegrityIssue(
                    category="missing_document",
                    entity_type="contract",
                    entity_id=c.id,
                    message="Contract missing document_url",
                )
            )
    return issues


def generate_integrity_report(db: Session) -> IntegrityReport:
    issues: List[IntegrityIssue] = []

    issues.extend(check_wholesale_integrity(db))
    issues.extend(check_retainer_integrity(db))
    issues.extend(check_contract_integrity(db))

    return IntegrityReport(total_issues=len(issues), issues=issues)
