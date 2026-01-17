from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GodReviewEventBase(BaseModel):
    actor: str = Field(..., description="heimdall | loki | human | system")
    event_type: str = Field(
        ...,
        description="suggestion | review | override | comment | decision | sync",
    )
    message: Optional[str] = None
    payload: Optional[dict[str, Any]] = None


class GodReviewEventCreate(GodReviewEventBase):
    pass


class GodReviewEventRead(GodReviewEventBase):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class GodReviewCaseBase(BaseModel):
    subject_type: str = Field(
        ...,
        description="What this is about: deal, contract, tax_plan, automation_change, etc.",
    )
    subject_reference: Optional[str] = Field(
        default=None,
        description="ID or reference Heimdall uses to link back to the object.",
    )
    title: str
    description: Optional[str] = None


class GodReviewCaseCreate(GodReviewCaseBase):
    heimdall_summary: Optional[str] = None
    heimdall_payload: Optional[dict[str, Any]] = None


class GodReviewCaseUpdate(BaseModel):
    status: Optional[str] = None
    final_outcome: Optional[str] = None
    final_notes: Optional[str] = None
    loki_summary: Optional[str] = None
    loki_payload: Optional[dict[str, Any]] = None
    human_summary: Optional[str] = None
    human_payload: Optional[dict[str, Any]] = None


class GodReviewCaseRead(GodReviewCaseBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    status: str
    heimdall_summary: Optional[str] = None
    loki_summary: Optional[str] = None
    human_summary: Optional[str] = None

    heimdall_payload: Optional[dict[str, Any]] = None
    loki_payload: Optional[dict[str, Any]] = None
    human_payload: Optional[dict[str, Any]] = None

    final_outcome: str
    final_notes: Optional[str] = None

    events: List[GodReviewEventRead] = []

    model_config = {"from_attributes": True}


class GodReviewCaseListItem(BaseModel):
    id: UUID
    created_at: datetime
    subject_type: str
    subject_reference: Optional[str] = None
    title: str
    status: str
    final_outcome: str

    model_config = {"from_attributes": True}


class DualGodSnapshot(BaseModel):
    """
    Quick "what do the two gods + human say?" snapshot.
    Useful for dashboards and Heimdall's own logic.
    """

    case_id: UUID
    subject_type: str
    subject_reference: Optional[str] = None
    title: str

    heimdall_summary: Optional[str] = None
    loki_summary: Optional[str] = None
    human_summary: Optional[str] = None

    final_outcome: str
    status: str
