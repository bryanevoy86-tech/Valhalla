"""
PACK CL16: Compliance Evidence Vault
Stores evidence artifacts (monthly reports, receipts refs, invoices refs, progress summaries).
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from app.models.base import Base


class ComplianceEvidence(Base):
    __tablename__ = "compliance_evidence"

    id = Column(Integer, primary_key=True, index=True)

    evidence_id = Column(String, unique=True, index=True, nullable=False)

    # e.g. "EIA_MONTHLY_REPORT", "RECEIPT_BATCH", "INVOICE", "BANK_EXPORT", "QB_EXPORT"
    evidence_type = Column(String, nullable=False)

    # e.g. "2026-03" or "week_12"
    period = Column(String, nullable=True)

    title = Column(String, nullable=False)
    notes = Column(Text, nullable=True)

    # references: {"file":"s3://...", "local":"...", "qb_report_id":"...", "links":[...]}
    references = Column(JSON, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
