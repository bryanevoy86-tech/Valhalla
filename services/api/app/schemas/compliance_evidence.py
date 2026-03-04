"""
PACK CL16: Compliance Evidence Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ComplianceEvidenceCreate(BaseModel):
    evidence_id: str
    evidence_type: str
    period: Optional[str] = None
    title: str
    notes: Optional[str] = None
    references: Optional[Dict[str, Any]] = None


class ComplianceEvidenceOut(BaseModel):
    evidence_id: str
    evidence_type: str
    period: Optional[str] = None
    title: str
    notes: Optional[str] = None
    references: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ComplianceEvidenceList(BaseModel):
    total: int
    items: List[ComplianceEvidenceOut]
