"""
Pydantic v2 schemas for PACK SZ, TA, TB

Validation, regex patterns, and constraints for all models.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import List, Optional, Dict


# =============================================================================
# PACK SZ: Core Philosophy & "Why I Built Valhalla" Archive
# =============================================================================

class PhilosophyRecordCreate(BaseModel):
    """Create a philosophy record."""
    title: str = Field(..., min_length=1, max_length=255, description="Philosophy title")
    date: date = Field(..., description="Date record created")
    pillars: List[str] = Field(default_factory=list, description="Core beliefs")
    mission_statement: str = Field(..., min_length=1, description="Mission statement")
    values: List[str] = Field(default_factory=list, description="Core values")
    rules_to_follow: List[str] = Field(default_factory=list, description="Guiding rules")
    rules_to_never_break: List[str] = Field(default_factory=list, description="Non-negotiables")
    long_term_intent: str = Field(..., min_length=1, description="Long-term intent")
    notes: Optional[str] = Field(None, description="Additional notes")


class PhilosophyRecordUpdate(BaseModel):
    """Update a philosophy record."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    mission_statement: Optional[str] = Field(None, min_length=1)
    pillars: Optional[List[str]] = None
    values: Optional[List[str]] = None
    rules_to_follow: Optional[List[str]] = None
    rules_to_never_break: Optional[List[str]] = None
    long_term_intent: Optional[str] = Field(None, min_length=1)
    notes: Optional[str] = None


class PhilosophyRecordResponse(BaseModel):
    """Response model for philosophy record."""
    id: int
    record_id: str
    title: str
    date: date
    pillars: List[str]
    mission_statement: str
    values: List[str]
    rules_to_follow: List[str]
    rules_to_never_break: List[str]
    long_term_intent: str
    notes: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class EmpirePrincipleCreate(BaseModel):
    """Create an empire principle."""
    record_id: int = Field(..., description="Parent philosophy record ID")
    category: str = Field(
        ...,
        pattern="^(ethics|growth|family|wealth|behavior|decision_making)$",
        description="Principle category"
    )
    description: str = Field(..., min_length=1, description="Principle description")
    enforcement_level: str = Field(default="soft", pattern="^(soft|strong)$")
    notes: Optional[str] = Field(None, description="Additional notes")


class EmpirePrincipleUpdate(BaseModel):
    """Update an empire principle."""
    category: Optional[str] = Field(None, pattern="^(ethics|growth|family|wealth|behavior|decision_making)$")
    description: Optional[str] = Field(None, min_length=1)
    enforcement_level: Optional[str] = Field(None, pattern="^(soft|strong)$")
    notes: Optional[str] = None


class EmpirePrincipleResponse(BaseModel):
    """Response model for empire principle."""
    id: int
    principle_id: str
    record_id: int
    category: str
    description: str
    enforcement_level: str
    notes: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class PhilosophySnapshotCreate(BaseModel):
    """Create a philosophy snapshot."""
    date: date = Field(..., description="Snapshot date")
    core_pillars: List[str] = Field(default_factory=list, description="Current core beliefs")
    recent_updates: List[str] = Field(default_factory=list, description="Recent changes")
    impact_on_system: List[str] = Field(default_factory=list, description="System implications")
    user_notes: Optional[str] = Field(None, description="User notes")


class PhilosophySnapshotUpdate(BaseModel):
    """Update a philosophy snapshot."""
    core_pillars: Optional[List[str]] = None
    recent_updates: Optional[List[str]] = None
    impact_on_system: Optional[List[str]] = None
    user_notes: Optional[str] = None


class PhilosophySnapshotResponse(BaseModel):
    """Response model for philosophy snapshot."""
    id: int
    snapshot_id: str
    date: date
    core_pillars: List[str]
    recent_updates: List[str]
    impact_on_system: List[str]
    user_notes: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# PACK TA: Trust, Loyalty & Relationship Mapping
# =============================================================================

class RelationshipProfileCreate(BaseModel):
    """Create a relationship profile."""
    name: str = Field(..., min_length=1, max_length=255, description="Person's name")
    role: str = Field(..., min_length=1, max_length=64, description="Role (friend, family, etc.)")
    relationship_type: str = Field(
        ...,
        pattern="^(supportive|distant|transactional|professional|family)$",
        description="Relationship type"
    )
    user_defined_trust_level: int = Field(..., ge=1, le=10, description="Trust level (1-10)")
    boundaries: List[str] = Field(default_factory=list, description="User-defined boundaries")
    notes: Optional[str] = Field(None, description="Additional notes")


class RelationshipProfileUpdate(BaseModel):
    """Update a relationship profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, min_length=1, max_length=64)
    relationship_type: Optional[str] = Field(None, pattern="^(supportive|distant|transactional|professional|family)$")
    user_defined_trust_level: Optional[int] = Field(None, ge=1, le=10)
    boundaries: Optional[List[str]] = None
    notes: Optional[str] = None


class RelationshipProfileResponse(BaseModel):
    """Response model for relationship profile."""
    id: int
    profile_id: str
    name: str
    role: str
    relationship_type: str
    user_defined_trust_level: int
    boundaries: List[str]
    notes: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class TrustEventLogCreate(BaseModel):
    """Create a trust event log entry."""
    profile_id: int = Field(..., description="Relationship profile ID")
    date: date = Field(..., description="Event date")
    event_description: str = Field(..., min_length=1, description="What happened")
    trust_change: int = Field(..., ge=-10, le=10, description="Trust impact (-10 to +10)")
    notes: Optional[str] = Field(None, description="Additional notes")


class TrustEventLogUpdate(BaseModel):
    """Update a trust event log entry."""
    event_description: Optional[str] = Field(None, min_length=1)
    trust_change: Optional[int] = Field(None, ge=-10, le=10)
    notes: Optional[str] = None


class TrustEventLogResponse(BaseModel):
    """Response model for trust event log."""
    id: int
    event_id: str
    profile_id: int
    date: date
    event_description: str
    trust_change: int
    notes: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class RelationshipMapSnapshotCreate(BaseModel):
    """Create a relationship map snapshot."""
    date: date = Field(..., description="Snapshot date")
    key_people: List[str] = Field(default_factory=list, description="Key people names")
    trust_levels: Dict[str, int] = Field(default_factory=dict, description="Trust levels by name")
    boundaries: Dict[str, List[str]] = Field(default_factory=dict, description="Boundaries by name")
    notes: Optional[str] = Field(None, description="Additional notes")


class RelationshipMapSnapshotUpdate(BaseModel):
    """Update a relationship map snapshot."""
    key_people: Optional[List[str]] = None
    trust_levels: Optional[Dict[str, int]] = None
    boundaries: Optional[Dict[str, List[str]]] = None
    notes: Optional[str] = None


class RelationshipMapSnapshotResponse(BaseModel):
    """Response model for relationship map snapshot."""
    id: int
    snapshot_id: str
    date: date
    key_people: List[str]
    trust_levels: Dict[str, int]
    boundaries: Dict[str, List[str]]
    notes: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# PACK TB: Daily Behavioral Rhythm & Tempo Engine
# =============================================================================

class TimeBlock(BaseModel):
    """Time block model."""
    start: str = Field(..., pattern="^([0-1][0-9]|2[0-3]):[0-5][0-9]$", description="Start time (HH:MM)")
    end: str = Field(..., pattern="^([0-1][0-9]|2[0-3]):[0-5][0-9]$", description="End time (HH:MM)")


class DailyRhythmProfileCreate(BaseModel):
    """Create a daily rhythm profile."""
    wake_time: str = Field(..., pattern="^([0-1][0-9]|2[0-3]):[0-5][0-9]$", description="Wake time")
    sleep_time: str = Field(..., pattern="^([0-1][0-9]|2[0-3]):[0-5][0-9]$", description="Sleep time")
    peak_focus_blocks: List[TimeBlock] = Field(default_factory=list, description="Peak focus time blocks")
    low_energy_blocks: List[TimeBlock] = Field(default_factory=list, description="Low energy blocks")
    family_blocks: List[TimeBlock] = Field(default_factory=list, description="Family time blocks")
    personal_time_blocks: List[TimeBlock] = Field(default_factory=list, description="Personal time blocks")
    notes: Optional[str] = Field(None, description="Additional notes")


class DailyRhythmProfileUpdate(BaseModel):
    """Update a daily rhythm profile."""
    wake_time: Optional[str] = Field(None, pattern="^([0-1][0-9]|2[0-3]):[0-5][0-9]$")
    sleep_time: Optional[str] = Field(None, pattern="^([0-1][0-9]|2[0-3]):[0-5][0-9]$")
    peak_focus_blocks: Optional[List[TimeBlock]] = None
    low_energy_blocks: Optional[List[TimeBlock]] = None
    family_blocks: Optional[List[TimeBlock]] = None
    personal_time_blocks: Optional[List[TimeBlock]] = None
    notes: Optional[str] = None


class DailyRhythmProfileResponse(BaseModel):
    """Response model for daily rhythm profile."""
    id: int
    profile_id: str
    wake_time: str
    sleep_time: str
    peak_focus_blocks: List[Dict]
    low_energy_blocks: List[Dict]
    family_blocks: List[Dict]
    personal_time_blocks: List[Dict]
    notes: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class TempoRuleCreate(BaseModel):
    """Create a tempo rule."""
    profile_id: int = Field(..., description="Daily rhythm profile ID")
    time_block: str = Field(
        ...,
        pattern="^(morning|afternoon|evening|night)$",
        description="Time of day"
    )
    action_intensity: str = Field(
        ...,
        pattern="^(push|balanced|gentle)$",
        description="Action intensity"
    )
    communication_style: str = Field(
        ...,
        pattern="^(short|detailed|none|check_in)$",
        description="Communication style"
    )
    notes: Optional[str] = Field(None, description="Additional notes")


class TempoRuleUpdate(BaseModel):
    """Update a tempo rule."""
    time_block: Optional[str] = Field(None, pattern="^(morning|afternoon|evening|night)$")
    action_intensity: Optional[str] = Field(None, pattern="^(push|balanced|gentle)$")
    communication_style: Optional[str] = Field(None, pattern="^(short|detailed|none|check_in)$")
    notes: Optional[str] = None


class TempoRuleResponse(BaseModel):
    """Response model for tempo rule."""
    id: int
    rule_id: str
    profile_id: int
    time_block: str
    action_intensity: str
    communication_style: str
    notes: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class DailyTempoSnapshotCreate(BaseModel):
    """Create a daily tempo snapshot."""
    date: date = Field(..., description="Snapshot date")
    rhythm_followed: bool = Field(default=True, description="Was rhythm followed?")
    adjustments_needed: Optional[str] = Field(None, description="Any adjustments needed?")
    user_notes: Optional[str] = Field(None, description="User notes")


class DailyTempoSnapshotUpdate(BaseModel):
    """Update a daily tempo snapshot."""
    rhythm_followed: Optional[bool] = None
    adjustments_needed: Optional[str] = None
    user_notes: Optional[str] = None


class DailyTempoSnapshotResponse(BaseModel):
    """Response model for daily tempo snapshot."""
    id: int
    snapshot_id: str
    date: date
    rhythm_followed: bool
    adjustments_needed: Optional[str]
    user_notes: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
