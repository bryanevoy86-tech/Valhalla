from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaxOpinionCreate(BaseModel):
    jurisdiction: str
    tax_year: Optional[str] = None

    source: str  # "accountant" | "ai" | "lawyer"
    specialist_id: Optional[UUID] = None
    case_id: Optional[UUID] = None

    summary: Optional[str] = None
    details: Optional[dict[str, Any]] = None

    risk_level: Optional[str] = None
    flags: Optional[dict[str, Any]] = None


class TaxOpinionRead(BaseModel):
    id: UUID
    created_at: datetime

    jurisdiction: str
    tax_year: Optional[str] = None

    source: str
    specialist_id: Optional[UUID] = None
    case_id: Optional[UUID] = None

    summary: Optional[str] = None
    details: Optional[dict[str, Any]] = None

    risk_level: Optional[str] = None
    flags: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class TaxOpinionProvenanceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation_id: UUID
    attachment_id: UUID
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    signer_key_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{3,80}$")
    issued_on: date
    valid_until: date
    signature: str = Field(pattern=r"^[a-f0-9]{128}$")



class TaxOpinionRelianceScope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_reference: str = Field(pattern=r"^[A-Za-z0-9_-]{3,100}$")
    purpose: Literal["INTERNAL_TAX_PLANNING", "INTERNAL_STRUCTURE_REVIEW", "INTERNAL_RISK_ASSESSMENT"]


class TaxOpinionRelianceIn(TaxOpinionRelianceScope):
    approval_id: UUID
    expected_provenance_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewer_key_id: str = Field(pattern=r"^[A-Za-z0-9_-]{3,80}$")
    reviewed_on: date
    valid_until: date
    signature: str = Field(pattern=r"^[a-f0-9]{128}$")


class TaxOpinionRelianceRevoke(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    reason: str = Field(min_length=5, max_length=500)
