"""
Pydantic v2 schemas for PACK SW, SX, SY

Validation, regex patterns, and constraints for all models.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import List, Optional


# =============================================================================
# PACK SW: Life Timeline & Major Milestones Engine
# =============================================================================

class LifeEventCreate(BaseModel):
    """Create a life event."""
    title: str = Field(..., min_length=1, max_length=255, description="Event title")
    date: date = Field(..., description="Event date")
    category: str = Field(
        ...,
        pattern="^(personal|family|business|financial|health|achievement)$",
        description="Event category"
    )
    description: str = Field(..., min_length=1, description="Factual description")
    impact_level: int = Field(default=1, ge=1, le=5, description="User-defined impact (1-5)")
    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        allowed = {"personal", "family", "business", "financial", "health", "achievement"}
        if v not in allowed:
            raise ValueError(f"Category must be one of {allowed}")
        return v


class LifeEventUpdate(BaseModel):
    """Update a life event."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    date: Optional[date] = None
    category: Optional[str] = Field(None, pattern="^(personal|family|business|financial|health|achievement)$")
    description: Optional[str] = Field(None, min_length=1)
    impact_level: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None


class LifeEventResponse(BaseModel):
    """Response model for life event."""
    id: int
    event_id: str
    date: date
    title: str
    category: str
    description: str
    impact_level: int
    notes: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class LifeMilestoneCreate(BaseModel):
    """Create a life milestone."""
    event_id: int = Field(..., description="Parent event ID")
    milestone_type: str = Field(
        ...,
        pattern="^(start|finish|transition|achievement)$",
        description="Milestone type"
    )
    description: str = Field(..., min_length=1, description="Milestone description")
    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator("milestone_type")
    @classmethod
    def validate_type(cls, v):
        allowed = {"start", "finish", "transition", "achievement"}
        if v not in allowed:
            raise ValueError(f"Milestone type must be one of {allowed}")
        return v


class LifeMilestoneUpdate(BaseModel):
    """Update a life milestone."""
    milestone_type: Optional[str] = Field(None, pattern="^(start|finish|transition|achievement)$")
    description: Optional[str] = Field(None, min_length=1)
    notes: Optional[str] = None


class LifeMilestoneResponse(BaseModel):
    """Response model for life milestone."""
    id: int
    milestone_id: str
    event_id: int
    milestone_type: str
    description: str
    notes: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class LifeTimelineSnapshotCreate(BaseModel):
    """Create a timeline snapshot."""
    date_generated: date = Field(..., description="Date snapshot was generated")
    major_events: List[str] = Field(default_factory=list, description="Event IDs")
    recent_changes: List[str] = Field(default_factory=list, description="Recent changes")
    upcoming_milestones: List[str] = Field(default_factory=list, description="Upcoming milestones")
    user_notes: Optional[str] = Field(None, description="User notes")


class LifeTimelineSnapshotUpdate(BaseModel):
    """Update a timeline snapshot."""
    major_events: Optional[List[str]] = None
    recent_changes: Optional[List[str]] = None
    upcoming_milestones: Optional[List[str]] = None
    user_notes: Optional[str] = None


class LifeTimelineSnapshotResponse(BaseModel):
    """Response model for timeline snapshot."""
    id: int
    snapshot_id: str
    date_generated: date
    major_events: List[str]
    recent_changes: List[str]
    upcoming_milestones: List[str]
    user_notes: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# PACK SX: Emotional Neutrality & Stability Log
# =============================================================================

class EmotionalStateEntryCreate(BaseModel):
    """Create an emotional state entry."""
    date: date = Field(..., description="Date of entry")
    self_reported_mood: str = Field(..., min_length=1, max_length=255, description="User's mood (own words)")
    energy_level: int = Field(..., ge=1, le=10, description="Energy level (1-10)")
    cognitive_load: int = Field(..., ge=1, le=10, description="Cognitive load (1-10)")
    context: str = Field(..., min_length=1, description="What's happening (factual)")
    notes: Optional[str] = Field(None, description="Additional notes")


class EmotionalStateEntryUpdate(BaseModel):
    """Update an emotional state entry."""
    self_reported_mood: Optional[str] = Field(None, min_length=1, max_length=255)
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    cognitive_load: Optional[int] = Field(None, ge=1, le=10)
    context: Optional[str] = Field(None, min_length=1)
    notes: Optional[str] = None


class EmotionalStateEntryResponse(BaseModel):
    """Response model for emotional state entry."""
    id: int
    entry_id: str
    date: date
    self_reported_mood: str
    energy_level: int
    cognitive_load: int
    context: str
    notes: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class StabilityLogCreate(BaseModel):
    """Create a stability log entry."""
    date: date = Field(..., description="Date of entry")
    events_today: List[str] = Field(default_factory=list, description="Events today")
    stress_factors: List[str] = Field(default_factory=list, description="Stress factors")
    relief_actions: List[str] = Field(default_factory=list, description="Relief actions")
    notes: Optional[str] = Field(None, description="Additional notes")


class StabilityLogUpdate(BaseModel):
    """Update a stability log entry."""
    events_today: Optional[List[str]] = None
    stress_factors: Optional[List[str]] = None
    relief_actions: Optional[List[str]] = None
    notes: Optional[str] = None


class StabilityLogResponse(BaseModel):
    """Response model for stability log."""
    id: int
    log_id: str
    date: date
    events_today: List[str]
    stress_factors: List[str]
    relief_actions: List[str]
    notes: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class NeutralSummaryCreate(BaseModel):
    """Create a neutral summary."""
    week_of: str = Field(..., pattern="^\\d{4}-W\\d{2}$", description="Week format: YYYY-WXX")
    average_energy: float = Field(default=0.0, ge=0.0, le=10.0, description="Average energy")
    task_load: float = Field(default=0.0, ge=0.0, le=10.0, description="Task load")
    user_highlights: List[str] = Field(default_factory=list, description="User-identified positives")
    user_defined_interpretation: Optional[str] = Field(None, description="User's interpretation")


class NeutralSummaryUpdate(BaseModel):
    """Update a neutral summary."""
    average_energy: Optional[float] = Field(None, ge=0.0, le=10.0)
    task_load: Optional[float] = Field(None, ge=0.0, le=10.0)
    user_highlights: Optional[List[str]] = None
    user_defined_interpretation: Optional[str] = None


class NeutralSummaryResponse(BaseModel):
    """Response model for neutral summary."""
    id: int
    summary_id: str
    week_of: str
    average_energy: float
    task_load: float
    user_highlights: List[str]
    user_defined_interpretation: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# PACK SY: Strategic Decision History & Reason Archive
# =============================================================================

class StrategicDecisionCreate(BaseModel):
    """Create a strategic decision record."""
    date: date = Field(..., description="Decision date")
    title: str = Field(..., min_length=1, max_length=255, description="Decision title")
    category: str = Field(
        ...,
        pattern="^(business|family|finance|real_estate|system)$",
        description="Decision category"
    )
    reasoning: str = Field(..., min_length=1, description="User-stated rationale")
    alternatives_considered: List[str] = Field(default_factory=list, description="Alternatives")
    constraints: List[str] = Field(default_factory=list, description="Constraints at time")
    expected_outcome: str = Field(..., min_length=1, description="Expected outcome")
    status: str = Field(default="active", pattern="^(active|revised|reversed|completed)$")
    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        allowed = {"business", "family", "finance", "real_estate", "system"}
        if v not in allowed:
            raise ValueError(f"Category must be one of {allowed}")
        return v


class StrategicDecisionUpdate(BaseModel):
    """Update a strategic decision."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    reasoning: Optional[str] = Field(None, min_length=1)
    alternatives_considered: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    expected_outcome: Optional[str] = Field(None, min_length=1)
    status: Optional[str] = Field(None, pattern="^(active|revised|reversed|completed)$")
    notes: Optional[str] = None


class StrategicDecisionResponse(BaseModel):
    """Response model for strategic decision."""
    id: int
    decision_id: str
    date: date
    title: str
    category: str
    reasoning: str
    alternatives_considered: List[str]
    constraints: List[str]
    expected_outcome: str
    status: str
    notes: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class DecisionRevisionCreate(BaseModel):
    """Create a decision revision record."""
    decision_id: int = Field(..., description="Parent decision ID")
    date: date = Field(..., description="Revision date")
    reason_for_revision: str = Field(..., min_length=1, description="Why you changed course")
    what_changed: str = Field(..., min_length=1, description="What specifically changed")
    notes: Optional[str] = Field(None, description="Additional notes")


class DecisionRevisionUpdate(BaseModel):
    """Update a decision revision."""
    reason_for_revision: Optional[str] = Field(None, min_length=1)
    what_changed: Optional[str] = Field(None, min_length=1)
    notes: Optional[str] = None


class DecisionRevisionResponse(BaseModel):
    """Response model for decision revision."""
    id: int
    revision_id: str
    decision_id: int
    date: date
    reason_for_revision: str
    what_changed: str
    notes: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class DecisionChainSnapshotCreate(BaseModel):
    """Create a decision chain snapshot."""
    date: date = Field(..., description="Snapshot date")
    major_decisions: List[str] = Field(default_factory=list, description="Major decisions")
    revisions: List[str] = Field(default_factory=list, description="Evolution record")
    reasons: List[str] = Field(default_factory=list, description="User-stated reasons")
    system_impacts: List[str] = Field(default_factory=list, description="Empire impacts")


class DecisionChainSnapshotUpdate(BaseModel):
    """Update a decision chain snapshot."""
    major_decisions: Optional[List[str]] = None
    revisions: Optional[List[str]] = None
    reasons: Optional[List[str]] = None
    system_impacts: Optional[List[str]] = None


class DecisionChainSnapshotResponse(BaseModel):
    """Response model for decision chain snapshot."""
    id: int
    snapshot_id: str
    date: date
    major_decisions: List[str]
    revisions: List[str]
    reasons: List[str]
    system_impacts: List[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
