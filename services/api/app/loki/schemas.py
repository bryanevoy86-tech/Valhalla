"""Loki AI review Pydantic schemas for request/response validation."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LokiFindingBase(BaseModel):
    """Base schema for Loki findings."""
    category: str
    severity: str
    message: str
    suggested_fix: Optional[str] = None
    tags: Optional[dict[str, Any]] = None


class LokiFindingCreate(LokiFindingBase):
    """Schema for creating a new Loki finding."""
    pass


class LokiFindingRead(LokiFindingBase):
    """Schema for reading a Loki finding with database fields."""
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class LokiReviewBase(BaseModel):
    """Base schema for Loki reviews."""
    input_source: str = Field(
        ...,
        description="Who generated this artifact (heimdall module, external expert, etc.)",
    )
    artifact_type: str = Field(
        ...,
        description="Classification: deal, contract, tax_plan, trust, automation_change, etc.",
    )
    risk_profile: Optional[str] = Field(
        default="default",
        description="Risk mode, e.g. default, aggressive_but_safe, ultra_conservative",
    )
    raw_input: dict


class LokiReviewCreate(LokiReviewBase):
    """Schema for creating a new Loki review."""
    requested_checks: Optional[list[str]] = Field(
        default=None,
        description="Optional list of specific checks Loki should run.",
    )
    heimdall_reference_id: Optional[str] = None
    human_reference_id: Optional[str] = None


class LokiReviewRead(LokiReviewBase):
    """Schema for reading a Loki review with all database fields."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    status: str
    heimdall_reference_id: Optional[str] = None
    human_reference_id: Optional[str] = None
    summary: Optional[str] = None
    result_severity: Optional[str] = None
    raw_output: Optional[dict] = None
    findings: list[LokiFindingRead] = []

    model_config = {"from_attributes": True}


class LokiReviewListItem(BaseModel):
    """Lightweight schema for listing Loki reviews."""
    id: UUID
    created_at: datetime
    artifact_type: str
    input_source: str
    status: str
    result_severity: Optional[str] = None
    summary: Optional[str] = None

    model_config = {"from_attributes": True}


class LokiVerdict(BaseModel):
    """Final verdict schema from Loki analysis."""
    result_severity: str
    headline: str
    ok_to_proceed: bool
    requires_human_review: bool
    key_risks: list[str] = []
