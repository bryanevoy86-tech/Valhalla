"""
PACK CL18: EIA Monthly Report Generator
Creates a compliance evidence entry representing the monthly report snapshot.
"""

from datetime import datetime
from sqlalchemy.orm import Session

from app.models.compliance_evidence import ComplianceEvidence


def generate_monthly_report(db: Session, period: str, title: str, notes: str | None = None) -> ComplianceEvidence:
    evidence_id = f"eia_report_{period}_{int(datetime.utcnow().timestamp())}"

    # Placeholder summary structure.
    # Later we can enrich this by pulling QB exports, lead stats, and activity logs.
    references = {
        "period": period,
        "generated_at_utc": datetime.utcnow().isoformat() + "Z",
        "sections": [
            "Business activity summary",
            "Revenue/expense snapshot (net after expenses)",
            "Receipts & invoices attached (references)",
            "Progress milestones",
        ],
    }

    obj = ComplianceEvidence(
        evidence_id=evidence_id,
        evidence_type="EIA_MONTHLY_REPORT",
        period=period,
        title=title,
        notes=notes,
        references=references,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
