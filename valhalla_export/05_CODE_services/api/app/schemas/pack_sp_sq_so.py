"""
Pydantic v2 schemas for PACK SP, SQ, SO

Includes request/response models with proper validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# PACK SP: Crisis Management Schemas
# ============================================================================

class SeverityLevel(BaseModel):
    """Represents a severity level for a crisis."""
    level: int
    description: str


class CrisisProfileCreate(BaseModel):
    """Create a new crisis profile."""
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., pattern="^(family|health|financial|legal|operations|unexpected)$")
    triggers: Optional[List[str]] = None
    severity_levels: Optional[List[SeverityLevel]] = None
    notes: Optional[str] = None


class CrisisProfileUpdate(BaseModel):
    """Update a crisis profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, pattern="^(family|health|financial|legal|operations|unexpected)$")
    triggers: Optional[List[str]] = None
    severity_levels: Optional[List[SeverityLevel]] = None
    notes: Optional[str] = None


class CrisisProfileResponse(CrisisProfileCreate):
    """Response model for crisis profile."""
    id: int
    crisis_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CrisisActionStepCreate(BaseModel):
    """Create a crisis action step."""
    crisis_id: int
    order: int = Field(..., ge=1)
    action: str = Field(..., min_length=1)
    responsible_role: str = Field(..., pattern="^(King|Queen|Odin|VA|Heimdall)$")
    notes: Optional[str] = None


class CrisisActionStepUpdate(BaseModel):
    """Update a crisis action step."""
    order: Optional[int] = Field(None, ge=1)
    action: Optional[str] = Field(None, min_length=1)
    responsible_role: Optional[str] = Field(None, pattern="^(King|Queen|Odin|VA|Heimdall)$")
    notes: Optional[str] = None


class CrisisActionStepResponse(CrisisActionStepCreate):
    """Response model for crisis action step."""
    id: int
    step_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CrisisLogEntryCreate(BaseModel):
    """Create a crisis log entry."""
    crisis_id: int
    date: datetime
    event: str = Field(..., min_length=1)
    actions_taken: Optional[List[str]] = None
    status: Optional[str] = Field("active", pattern="^(active|resolved)$")
    notes: Optional[str] = None


class CrisisLogEntryResponse(CrisisLogEntryCreate):
    """Response model for crisis log entry."""
    id: int
    log_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class CrisisWorkflowCreate(BaseModel):
    """Create a crisis workflow."""
    crisis_id: str = Field(..., min_length=1, max_length=255)
    current_step: Optional[int] = None
    status: Optional[str] = Field("intake", pattern="^(intake|executing|paused|completed)$")
    triggered_date: Optional[datetime] = None


class CrisisWorkflowUpdate(BaseModel):
    """Update a crisis workflow."""
    current_step: Optional[int] = None
    status: Optional[str] = Field(None, pattern="^(intake|executing|paused|completed)$")
    triggered_date: Optional[datetime] = None
    steps_completed: Optional[int] = Field(None, ge=0)
    completion_notes: Optional[str] = None


class CrisisWorkflowResponse(CrisisWorkflowCreate):
    """Response model for crisis workflow."""
    id: int
    workflow_id: str
    steps_completed: int
    completion_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PACK SQ: Partner/Marriage Stability Ops Schemas
# ============================================================================

class SharedDomain(BaseModel):
    """Shared responsibility domain."""
    domain: str
    primary_responsible: str
    secondary_responsible: Optional[str] = None


class CommunicationProtocol(BaseModel):
    """Communication guidelines for specific context."""
    context: str
    preferred_method: str
    notes: Optional[str] = None


class RelationshipOpsProfileCreate(BaseModel):
    """Create a relationship ops profile."""
    partner_name: str = Field(..., min_length=1, max_length=255)
    shared_domains: Optional[List[SharedDomain]] = None
    communication_protocol: Optional[List[CommunicationProtocol]] = None
    boundaries: Optional[List[str]] = None
    notes: Optional[str] = None


class RelationshipOpsProfileUpdate(BaseModel):
    """Update a relationship ops profile."""
    partner_name: Optional[str] = Field(None, min_length=1, max_length=255)
    shared_domains: Optional[List[SharedDomain]] = None
    communication_protocol: Optional[List[CommunicationProtocol]] = None
    boundaries: Optional[List[str]] = None
    notes: Optional[str] = None


class RelationshipOpsProfileResponse(RelationshipOpsProfileCreate):
    """Response model for relationship ops profile."""
    id: int
    profile_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CoParentingDay(BaseModel):
    """Daily co-parenting schedule."""
    day: str
    responsible_parent: str
    pickup_time: Optional[str] = None
    dropoff_time: Optional[str] = None


class CoParentingScheduleCreate(BaseModel):
    """Create a co-parenting schedule."""
    profile_id: int
    days: Optional[List[CoParentingDay]] = None
    special_rules: Optional[List[str]] = None
    notes: Optional[str] = None


class CoParentingScheduleUpdate(BaseModel):
    """Update a co-parenting schedule."""
    days: Optional[List[CoParentingDay]] = None
    special_rules: Optional[List[str]] = None
    notes: Optional[str] = None


class CoParentingScheduleResponse(CoParentingScheduleCreate):
    """Response model for co-parenting schedule."""
    id: int
    schedule_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HouseholdResponsibilityCreate(BaseModel):
    """Create a household responsibility."""
    profile_id: int
    task: str = Field(..., min_length=1, max_length=255)
    frequency: str = Field(..., pattern="^(daily|weekly|monthly|as_needed)$")
    primary_responsible: str = Field(..., min_length=1)
    fallback_responsible: Optional[str] = None
    notes: Optional[str] = None


class HouseholdResponsibilityUpdate(BaseModel):
    """Update a household responsibility."""
    task: Optional[str] = Field(None, min_length=1, max_length=255)
    frequency: Optional[str] = Field(None, pattern="^(daily|weekly|monthly|as_needed)$")
    primary_responsible: Optional[str] = Field(None, min_length=1)
    fallback_responsible: Optional[str] = None
    notes: Optional[str] = None


class HouseholdResponsibilityResponse(HouseholdResponsibilityCreate):
    """Response model for household responsibility."""
    id: int
    task_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommunicationLogCreate(BaseModel):
    """Create a communication log."""
    profile_id: int
    date: datetime
    topic: str = Field(..., min_length=1, max_length=255)
    summary: Optional[str] = None
    follow_up_required: Optional[bool] = False
    notes: Optional[str] = None


class CommunicationLogResponse(CommunicationLogCreate):
    """Response model for communication log."""
    id: int
    log_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PACK SO: Legacy & Succession Archive Schemas
# ============================================================================

class KnowledgeDomain(BaseModel):
    """Area of knowledge to preserve."""
    domain: str
    description: Optional[str] = None
    notes: Optional[str] = None


class LegacyProfileCreate(BaseModel):
    """Create a legacy profile."""
    description: Optional[str] = None
    long_term_goals: Optional[List[str]] = None
    knowledge_domains: Optional[List[KnowledgeDomain]] = None
    heir_candidates: Optional[List[str]] = None
    notes: Optional[str] = None


class LegacyProfileUpdate(BaseModel):
    """Update a legacy profile."""
    description: Optional[str] = None
    long_term_goals: Optional[List[str]] = None
    knowledge_domains: Optional[List[KnowledgeDomain]] = None
    heir_candidates: Optional[List[str]] = None
    notes: Optional[str] = None


class LegacyProfileResponse(LegacyProfileCreate):
    """Response model for legacy profile."""
    id: int
    legacy_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgePackageCreate(BaseModel):
    """Create a knowledge package."""
    legacy_id: int
    title: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., pattern="^(finance|family|values|system_design|decision_making)$")
    content: str = Field(..., min_length=1)
    notes: Optional[str] = None


class KnowledgePackageUpdate(BaseModel):
    """Update a knowledge package."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, pattern="^(finance|family|values|system_design|decision_making)$")
    content: Optional[str] = Field(None, min_length=1)
    notes: Optional[str] = None


class KnowledgePackageResponse(KnowledgePackageCreate):
    """Response model for knowledge package."""
    id: int
    package_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AccessLevel(BaseModel):
    """Module-level access definition."""
    module: str
    level: str  # read-only, supervised, none


class SuccessionStageCreate(BaseModel):
    """Create a succession stage."""
    legacy_id: int
    description: Optional[str] = None
    trigger: Optional[str] = None
    access_level: Optional[List[AccessLevel]] = None
    training_requirements: Optional[List[str]] = None
    notes: Optional[str] = None


class SuccessionStageUpdate(BaseModel):
    """Update a succession stage."""
    description: Optional[str] = None
    trigger: Optional[str] = None
    access_level: Optional[List[AccessLevel]] = None
    training_requirements: Optional[List[str]] = None
    notes: Optional[str] = None


class SuccessionStageResponse(SuccessionStageCreate):
    """Response model for succession stage."""
    id: int
    stage_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LegacyVaultCreate(BaseModel):
    """Create a legacy vault."""
    legacy_id: int
    packages: Optional[List[str]] = None
    successor_roles: Optional[List[str]] = None
    notes: Optional[str] = None


class LegacyVaultUpdate(BaseModel):
    """Update a legacy vault."""
    packages: Optional[List[str]] = None
    successor_roles: Optional[List[str]] = None
    notes: Optional[str] = None


class LegacyVaultResponse(LegacyVaultCreate):
    """Response model for legacy vault."""
    id: int
    vault_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
