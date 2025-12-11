"""
FastAPI routers for PACK SP, SQ, SO

Provides REST API endpoints for crisis management, relationship ops, and legacy/succession.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.schemas.pack_sp_sq_so import (
    CrisisProfileCreate, CrisisProfileUpdate, CrisisProfileResponse,
    CrisisActionStepCreate, CrisisActionStepUpdate, CrisisActionStepResponse,
    CrisisLogEntryCreate, CrisisLogEntryResponse,
    CrisisWorkflowCreate, CrisisWorkflowUpdate, CrisisWorkflowResponse,
    RelationshipOpsProfileCreate, RelationshipOpsProfileUpdate, RelationshipOpsProfileResponse,
    CoParentingScheduleCreate, CoParentingScheduleUpdate, CoParentingScheduleResponse,
    HouseholdResponsibilityCreate, HouseholdResponsibilityUpdate, HouseholdResponsibilityResponse,
    CommunicationLogCreate, CommunicationLogResponse,
    LegacyProfileCreate, LegacyProfileUpdate, LegacyProfileResponse,
    KnowledgePackageCreate, KnowledgePackageUpdate, KnowledgePackageResponse,
    SuccessionStageCreate, SuccessionStageUpdate, SuccessionStageResponse,
    LegacyVaultCreate, LegacyVaultUpdate, LegacyVaultResponse
)
from app.services.pack_sp_sq_so import (
    CrisisProfileService, CrisisActionStepService, CrisisLogEntryService, CrisisWorkflowService,
    RelationshipOpsProfileService, CoParentingScheduleService, HouseholdResponsibilityService, CommunicationLogService,
    LegacyProfileService, KnowledgePackageService, SuccessionStageService, LegacyVaultService
)


# ============================================================================
# PACK SP: Crisis Management Router
# ============================================================================

router_sp = APIRouter(prefix="/api/v1/crisis", tags=["Crisis Management"])


# Crisis Profiles
@router_sp.post("/profiles", response_model=CrisisProfileResponse, status_code=status.HTTP_201_CREATED)
def create_crisis_profile(data: CrisisProfileCreate, db: Session = Depends(get_db)):
    """Create a new crisis profile."""
    return CrisisProfileService.create(db, data)


@router_sp.get("/profiles", response_model=List[CrisisProfileResponse])
def list_crisis_profiles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all crisis profiles."""
    return CrisisProfileService.list_all(db, skip, limit)


@router_sp.get("/profiles/{profile_id}", response_model=CrisisProfileResponse)
def get_crisis_profile(profile_id: int, db: Session = Depends(get_db)):
    """Get a specific crisis profile."""
    profile = CrisisProfileService.get(db, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crisis profile not found")
    return profile


@router_sp.put("/profiles/{profile_id}", response_model=CrisisProfileResponse)
def update_crisis_profile(profile_id: int, data: CrisisProfileUpdate, db: Session = Depends(get_db)):
    """Update a crisis profile."""
    profile = CrisisProfileService.update(db, profile_id, data)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crisis profile not found")
    return profile


@router_sp.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crisis_profile(profile_id: int, db: Session = Depends(get_db)):
    """Delete a crisis profile."""
    if not CrisisProfileService.delete(db, profile_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crisis profile not found")


# Crisis Action Steps
@router_sp.post("/steps", response_model=CrisisActionStepResponse, status_code=status.HTTP_201_CREATED)
def create_action_step(data: CrisisActionStepCreate, db: Session = Depends(get_db)):
    """Create a new action step."""
    return CrisisActionStepService.create(db, data)


@router_sp.get("/steps/{step_id}", response_model=CrisisActionStepResponse)
def get_action_step(step_id: int, db: Session = Depends(get_db)):
    """Get a specific action step."""
    step = CrisisActionStepService.get(db, step_id)
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action step not found")
    return step


@router_sp.get("/crises/{crisis_id}/steps", response_model=List[CrisisActionStepResponse])
def list_crisis_steps(crisis_id: int, db: Session = Depends(get_db)):
    """List all steps for a crisis."""
    return CrisisActionStepService.list_by_crisis(db, crisis_id)


@router_sp.put("/steps/{step_id}", response_model=CrisisActionStepResponse)
def update_action_step(step_id: int, data: CrisisActionStepUpdate, db: Session = Depends(get_db)):
    """Update an action step."""
    step = CrisisActionStepService.update(db, step_id, data)
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action step not found")
    return step


@router_sp.delete("/steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_action_step(step_id: int, db: Session = Depends(get_db)):
    """Delete an action step."""
    if not CrisisActionStepService.delete(db, step_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action step not found")


# Crisis Log Entries
@router_sp.post("/logs", response_model=CrisisLogEntryResponse, status_code=status.HTTP_201_CREATED)
def create_log_entry(data: CrisisLogEntryCreate, db: Session = Depends(get_db)):
    """Create a new log entry."""
    return CrisisLogEntryService.create(db, data)


@router_sp.get("/logs/{entry_id}", response_model=CrisisLogEntryResponse)
def get_log_entry(entry_id: int, db: Session = Depends(get_db)):
    """Get a specific log entry."""
    entry = CrisisLogEntryService.get(db, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log entry not found")
    return entry


@router_sp.get("/crises/{crisis_id}/logs", response_model=List[CrisisLogEntryResponse])
def list_crisis_logs(crisis_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all log entries for a crisis."""
    return CrisisLogEntryService.list_by_crisis(db, crisis_id, skip, limit)


# Crisis Workflows
@router_sp.post("/workflows", response_model=CrisisWorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(data: CrisisWorkflowCreate, db: Session = Depends(get_db)):
    """Create a new crisis workflow."""
    return CrisisWorkflowService.create(db, data)


@router_sp.get("/workflows/{workflow_id}", response_model=CrisisWorkflowResponse)
def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """Get a specific workflow."""
    workflow = CrisisWorkflowService.get(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return workflow


@router_sp.put("/workflows/{workflow_id}", response_model=CrisisWorkflowResponse)
def update_workflow(workflow_id: int, data: CrisisWorkflowUpdate, db: Session = Depends(get_db)):
    """Update a crisis workflow."""
    workflow = CrisisWorkflowService.update(db, workflow_id, data)
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return workflow


# ============================================================================
# PACK SQ: Partner/Marriage Stability Ops Router
# ============================================================================

router_sq = APIRouter(prefix="/api/v1/partner", tags=["Partner/Marriage Ops"])


# Relationship Ops Profiles
@router_sq.post("/profiles", response_model=RelationshipOpsProfileResponse, status_code=status.HTTP_201_CREATED)
def create_relationship_profile(data: RelationshipOpsProfileCreate, db: Session = Depends(get_db)):
    """Create a new relationship ops profile."""
    return RelationshipOpsProfileService.create(db, data)


@router_sq.get("/profiles", response_model=List[RelationshipOpsProfileResponse])
def list_relationship_profiles(db: Session = Depends(get_db)):
    """List all relationship profiles."""
    return RelationshipOpsProfileService.list_all(db)


@router_sq.get("/profiles/{profile_id}", response_model=RelationshipOpsProfileResponse)
def get_relationship_profile(profile_id: int, db: Session = Depends(get_db)):
    """Get a specific relationship profile."""
    profile = RelationshipOpsProfileService.get(db, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relationship profile not found")
    return profile


@router_sq.put("/profiles/{profile_id}", response_model=RelationshipOpsProfileResponse)
def update_relationship_profile(profile_id: int, data: RelationshipOpsProfileUpdate, db: Session = Depends(get_db)):
    """Update a relationship profile."""
    profile = RelationshipOpsProfileService.update(db, profile_id, data)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relationship profile not found")
    return profile


# Co-Parenting Schedules
@router_sq.post("/schedules", response_model=CoParentingScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(data: CoParentingScheduleCreate, db: Session = Depends(get_db)):
    """Create a new co-parenting schedule."""
    return CoParentingScheduleService.create(db, data)


@router_sq.get("/schedules/{schedule_id}", response_model=CoParentingScheduleResponse)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Get a specific schedule."""
    schedule = CoParentingScheduleService.get(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    return schedule


@router_sq.get("/profiles/{profile_id}/schedule", response_model=CoParentingScheduleResponse)
def get_profile_schedule(profile_id: int, db: Session = Depends(get_db)):
    """Get schedule for a profile."""
    schedule = CoParentingScheduleService.get_by_profile(db, profile_id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    return schedule


@router_sq.put("/schedules/{schedule_id}", response_model=CoParentingScheduleResponse)
def update_schedule(schedule_id: int, data: CoParentingScheduleUpdate, db: Session = Depends(get_db)):
    """Update a schedule."""
    schedule = CoParentingScheduleService.update(db, schedule_id, data)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    return schedule


# Household Responsibilities
@router_sq.post("/responsibilities", response_model=HouseholdResponsibilityResponse, status_code=status.HTTP_201_CREATED)
def create_responsibility(data: HouseholdResponsibilityCreate, db: Session = Depends(get_db)):
    """Create a new household responsibility."""
    return HouseholdResponsibilityService.create(db, data)


@router_sq.get("/responsibilities/{responsibility_id}", response_model=HouseholdResponsibilityResponse)
def get_responsibility(responsibility_id: int, db: Session = Depends(get_db)):
    """Get a specific responsibility."""
    resp = HouseholdResponsibilityService.get(db, responsibility_id)
    if not resp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Responsibility not found")
    return resp


@router_sq.get("/profiles/{profile_id}/responsibilities", response_model=List[HouseholdResponsibilityResponse])
def list_profile_responsibilities(profile_id: int, db: Session = Depends(get_db)):
    """List responsibilities for a profile."""
    return HouseholdResponsibilityService.list_by_profile(db, profile_id)


@router_sq.put("/responsibilities/{responsibility_id}", response_model=HouseholdResponsibilityResponse)
def update_responsibility(responsibility_id: int, data: HouseholdResponsibilityUpdate, db: Session = Depends(get_db)):
    """Update a responsibility."""
    resp = HouseholdResponsibilityService.update(db, responsibility_id, data)
    if not resp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Responsibility not found")
    return resp


@router_sq.delete("/responsibilities/{responsibility_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_responsibility(responsibility_id: int, db: Session = Depends(get_db)):
    """Delete a responsibility."""
    if not HouseholdResponsibilityService.delete(db, responsibility_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Responsibility not found")


# Communication Logs
@router_sq.post("/communication", response_model=CommunicationLogResponse, status_code=status.HTTP_201_CREATED)
def create_communication_log(data: CommunicationLogCreate, db: Session = Depends(get_db)):
    """Create a new communication log entry."""
    return CommunicationLogService.create(db, data)


@router_sq.get("/communication/{entry_id}", response_model=CommunicationLogResponse)
def get_communication_log(entry_id: int, db: Session = Depends(get_db)):
    """Get a specific communication log entry."""
    entry = CommunicationLogService.get(db, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Communication log not found")
    return entry


@router_sq.get("/profiles/{profile_id}/communication", response_model=List[CommunicationLogResponse])
def list_profile_communication(profile_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List communication logs for a profile."""
    return CommunicationLogService.list_by_profile(db, profile_id, skip, limit)


# ============================================================================
# PACK SO: Legacy & Succession Archive Router
# ============================================================================

router_so = APIRouter(prefix="/api/v1/legacy", tags=["Legacy & Succession"])


# Legacy Profiles
@router_so.post("/profiles", response_model=LegacyProfileResponse, status_code=status.HTTP_201_CREATED)
def create_legacy_profile(data: LegacyProfileCreate, db: Session = Depends(get_db)):
    """Create a new legacy profile."""
    return LegacyProfileService.create(db, data)


@router_so.get("/profiles", response_model=List[LegacyProfileResponse])
def list_legacy_profiles(db: Session = Depends(get_db)):
    """List all legacy profiles."""
    return LegacyProfileService.list_all(db)


@router_so.get("/profiles/{profile_id}", response_model=LegacyProfileResponse)
def get_legacy_profile(profile_id: int, db: Session = Depends(get_db)):
    """Get a specific legacy profile."""
    profile = LegacyProfileService.get(db, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legacy profile not found")
    return profile


@router_so.put("/profiles/{profile_id}", response_model=LegacyProfileResponse)
def update_legacy_profile(profile_id: int, data: LegacyProfileUpdate, db: Session = Depends(get_db)):
    """Update a legacy profile."""
    profile = LegacyProfileService.update(db, profile_id, data)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legacy profile not found")
    return profile


# Knowledge Packages
@router_so.post("/packages", response_model=KnowledgePackageResponse, status_code=status.HTTP_201_CREATED)
def create_package(data: KnowledgePackageCreate, db: Session = Depends(get_db)):
    """Create a new knowledge package."""
    return KnowledgePackageService.create(db, data)


@router_so.get("/packages/{package_id}", response_model=KnowledgePackageResponse)
def get_package(package_id: int, db: Session = Depends(get_db)):
    """Get a specific package."""
    package = KnowledgePackageService.get(db, package_id)
    if not package:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge package not found")
    return package


@router_so.get("/profiles/{profile_id}/packages", response_model=List[KnowledgePackageResponse])
def list_profile_packages(profile_id: int, db: Session = Depends(get_db)):
    """List packages for a legacy profile."""
    return KnowledgePackageService.list_by_legacy(db, profile_id)


@router_so.put("/packages/{package_id}", response_model=KnowledgePackageResponse)
def update_package(package_id: int, data: KnowledgePackageUpdate, db: Session = Depends(get_db)):
    """Update a knowledge package."""
    package = KnowledgePackageService.update(db, package_id, data)
    if not package:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge package not found")
    return package


@router_so.delete("/packages/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(package_id: int, db: Session = Depends(get_db)):
    """Delete a knowledge package."""
    if not KnowledgePackageService.delete(db, package_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge package not found")


# Succession Stages
@router_so.post("/stages", response_model=SuccessionStageResponse, status_code=status.HTTP_201_CREATED)
def create_stage(data: SuccessionStageCreate, db: Session = Depends(get_db)):
    """Create a new succession stage."""
    return SuccessionStageService.create(db, data)


@router_so.get("/stages/{stage_id}", response_model=SuccessionStageResponse)
def get_stage(stage_id: int, db: Session = Depends(get_db)):
    """Get a specific stage."""
    stage = SuccessionStageService.get(db, stage_id)
    if not stage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Succession stage not found")
    return stage


@router_so.get("/profiles/{profile_id}/stages", response_model=List[SuccessionStageResponse])
def list_profile_stages(profile_id: int, db: Session = Depends(get_db)):
    """List stages for a legacy profile."""
    return SuccessionStageService.list_by_legacy(db, profile_id)


@router_so.put("/stages/{stage_id}", response_model=SuccessionStageResponse)
def update_stage(stage_id: int, data: SuccessionStageUpdate, db: Session = Depends(get_db)):
    """Update a succession stage."""
    stage = SuccessionStageService.update(db, stage_id, data)
    if not stage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Succession stage not found")
    return stage


@router_so.delete("/stages/{stage_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stage(stage_id: int, db: Session = Depends(get_db)):
    """Delete a succession stage."""
    if not SuccessionStageService.delete(db, stage_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Succession stage not found")


# Legacy Vaults
@router_so.post("/vaults", response_model=LegacyVaultResponse, status_code=status.HTTP_201_CREATED)
def create_vault(data: LegacyVaultCreate, db: Session = Depends(get_db)):
    """Create a new legacy vault."""
    return LegacyVaultService.create(db, data)


@router_so.get("/vaults/{vault_id}", response_model=LegacyVaultResponse)
def get_vault(vault_id: int, db: Session = Depends(get_db)):
    """Get a specific vault."""
    vault = LegacyVaultService.get(db, vault_id)
    if not vault:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legacy vault not found")
    return vault


@router_so.get("/profiles/{profile_id}/vault", response_model=LegacyVaultResponse)
def get_profile_vault(profile_id: int, db: Session = Depends(get_db)):
    """Get vault for a legacy profile."""
    vault = LegacyVaultService.get_by_legacy(db, profile_id)
    if not vault:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legacy vault not found")
    return vault


@router_so.put("/vaults/{vault_id}", response_model=LegacyVaultResponse)
def update_vault(vault_id: int, data: LegacyVaultUpdate, db: Session = Depends(get_db)):
    """Update a legacy vault."""
    vault = LegacyVaultService.update(db, vault_id, data)
    if not vault:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legacy vault not found")
    return vault
