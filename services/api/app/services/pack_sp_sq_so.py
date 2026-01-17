"""
Service functions for PACK SP, SQ, SO

Handles database operations and business logic.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import List, Optional

from app.models.pack_sp import CrisisProfile, CrisisActionStep, CrisisLogEntry, CrisisWorkflow
from app.models.pack_sq import RelationshipOpsProfile, CoParentingSchedule, HouseholdResponsibility, CommunicationLog
from app.models.pack_so_legacy import LegacyProfile, KnowledgePackage, SuccessionStage, LegacyVault
from app.schemas.pack_sp_sq_so import (
    CrisisProfileCreate, CrisisProfileUpdate, CrisisActionStepCreate, CrisisActionStepUpdate,
    CrisisLogEntryCreate, CrisisWorkflowCreate, CrisisWorkflowUpdate,
    RelationshipOpsProfileCreate, RelationshipOpsProfileUpdate, CoParentingScheduleCreate, CoParentingScheduleUpdate,
    HouseholdResponsibilityCreate, HouseholdResponsibilityUpdate, CommunicationLogCreate,
    LegacyProfileCreate, LegacyProfileUpdate, KnowledgePackageCreate, KnowledgePackageUpdate,
    SuccessionStageCreate, SuccessionStageUpdate, LegacyVaultCreate, LegacyVaultUpdate
)
from app.util.id_gen import generate_id


# ============================================================================
# PACK SP: Crisis Management Services
# ============================================================================

class CrisisProfileService:
    """Crisis profile management."""

    @staticmethod
    def create(db: Session, data: CrisisProfileCreate) -> CrisisProfile:
        """Create a new crisis profile."""
        profile = CrisisProfile(
            crisis_id=generate_id("crisis"),
            name=data.name,
            category=data.category,
            triggers=data.triggers,
            severity_levels=[sl.model_dump() for sl in data.severity_levels] if data.severity_levels else None,
            notes=data.notes
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get(db: Session, profile_id: int) -> Optional[CrisisProfile]:
        """Get crisis profile by ID."""
        return db.query(CrisisProfile).filter(CrisisProfile.id == profile_id).first()

    @staticmethod
    def get_by_crisis_id(db: Session, crisis_id: str) -> Optional[CrisisProfile]:
        """Get crisis profile by crisis_id."""
        return db.query(CrisisProfile).filter(CrisisProfile.crisis_id == crisis_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[CrisisProfile]:
        """List all crisis profiles."""
        return db.query(CrisisProfile).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, profile_id: int, data: CrisisProfileUpdate) -> Optional[CrisisProfile]:
        """Update a crisis profile."""
        profile = db.query(CrisisProfile).filter(CrisisProfile.id == profile_id).first()
        if not profile:
            return None
        
        if data.name is not None:
            profile.name = data.name
        if data.category is not None:
            profile.category = data.category
        if data.triggers is not None:
            profile.triggers = data.triggers
        if data.severity_levels is not None:
            profile.severity_levels = [sl.model_dump() for sl in data.severity_levels]
        if data.notes is not None:
            profile.notes = data.notes
        profile.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def delete(db: Session, profile_id: int) -> bool:
        """Delete a crisis profile."""
        profile = db.query(CrisisProfile).filter(CrisisProfile.id == profile_id).first()
        if not profile:
            return False
        db.delete(profile)
        db.commit()
        return True


class CrisisActionStepService:
    """Crisis action step management."""

    @staticmethod
    def create(db: Session, data: CrisisActionStepCreate) -> CrisisActionStep:
        """Create a new action step."""
        step = CrisisActionStep(
            step_id=generate_id("step"),
            crisis_id=data.crisis_id,
            order=data.order,
            action=data.action,
            responsible_role=data.responsible_role,
            notes=data.notes
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        return step

    @staticmethod
    def get(db: Session, step_id: int) -> Optional[CrisisActionStep]:
        """Get action step by ID."""
        return db.query(CrisisActionStep).filter(CrisisActionStep.id == step_id).first()

    @staticmethod
    def list_by_crisis(db: Session, crisis_id: int) -> List[CrisisActionStep]:
        """List steps for a crisis, ordered."""
        return db.query(CrisisActionStep)\
            .filter(CrisisActionStep.crisis_id == crisis_id)\
            .order_by(CrisisActionStep.order)\
            .all()

    @staticmethod
    def update(db: Session, step_id: int, data: CrisisActionStepUpdate) -> Optional[CrisisActionStep]:
        """Update an action step."""
        step = db.query(CrisisActionStep).filter(CrisisActionStep.id == step_id).first()
        if not step:
            return None
        
        if data.order is not None:
            step.order = data.order
        if data.action is not None:
            step.action = data.action
        if data.responsible_role is not None:
            step.responsible_role = data.responsible_role
        if data.notes is not None:
            step.notes = data.notes
        step.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(step)
        return step

    @staticmethod
    def delete(db: Session, step_id: int) -> bool:
        """Delete an action step."""
        step = db.query(CrisisActionStep).filter(CrisisActionStep.id == step_id).first()
        if not step:
            return False
        db.delete(step)
        db.commit()
        return True


class CrisisLogEntryService:
    """Crisis log entry management."""

    @staticmethod
    def create(db: Session, data: CrisisLogEntryCreate) -> CrisisLogEntry:
        """Create a new log entry."""
        entry = CrisisLogEntry(
            log_id=generate_id("log"),
            crisis_id=data.crisis_id,
            date=data.date,
            event=data.event,
            actions_taken=data.actions_taken,
            status=data.status or "active",
            notes=data.notes
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def get(db: Session, entry_id: int) -> Optional[CrisisLogEntry]:
        """Get log entry by ID."""
        return db.query(CrisisLogEntry).filter(CrisisLogEntry.id == entry_id).first()

    @staticmethod
    def list_by_crisis(db: Session, crisis_id: int, skip: int = 0, limit: int = 100) -> List[CrisisLogEntry]:
        """List entries for a crisis."""
        return db.query(CrisisLogEntry)\
            .filter(CrisisLogEntry.crisis_id == crisis_id)\
            .order_by(CrisisLogEntry.date.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()


class CrisisWorkflowService:
    """Crisis workflow management."""

    @staticmethod
    def create(db: Session, data: CrisisWorkflowCreate) -> CrisisWorkflow:
        """Create a new workflow."""
        workflow = CrisisWorkflow(
            workflow_id=generate_id("workflow"),
            crisis_id=data.crisis_id,
            current_step=data.current_step,
            status=data.status or "intake",
            triggered_date=data.triggered_date,
            steps_completed=0
        )
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        return workflow

    @staticmethod
    def get(db: Session, workflow_id: int) -> Optional[CrisisWorkflow]:
        """Get workflow by ID."""
        return db.query(CrisisWorkflow).filter(CrisisWorkflow.id == workflow_id).first()

    @staticmethod
    def update(db: Session, workflow_id: int, data: CrisisWorkflowUpdate) -> Optional[CrisisWorkflow]:
        """Update a workflow."""
        workflow = db.query(CrisisWorkflow).filter(CrisisWorkflow.id == workflow_id).first()
        if not workflow:
            return None
        
        if data.current_step is not None:
            workflow.current_step = data.current_step
        if data.status is not None:
            workflow.status = data.status
        if data.triggered_date is not None:
            workflow.triggered_date = data.triggered_date
        if data.steps_completed is not None:
            workflow.steps_completed = data.steps_completed
        if data.completion_notes is not None:
            workflow.completion_notes = data.completion_notes
        workflow.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(workflow)
        return workflow


# ============================================================================
# PACK SQ: Partner/Marriage Stability Ops Services
# ============================================================================

class RelationshipOpsProfileService:
    """Relationship ops profile management."""

    @staticmethod
    def create(db: Session, data: RelationshipOpsProfileCreate) -> RelationshipOpsProfile:
        """Create a new relationship profile."""
        profile = RelationshipOpsProfile(
            profile_id=generate_id("relops"),
            partner_name=data.partner_name,
            shared_domains=[d.model_dump() for d in data.shared_domains] if data.shared_domains else None,
            communication_protocol=[cp.model_dump() for cp in data.communication_protocol] if data.communication_protocol else None,
            boundaries=data.boundaries,
            notes=data.notes
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get(db: Session, profile_id: int) -> Optional[RelationshipOpsProfile]:
        """Get relationship profile by ID."""
        return db.query(RelationshipOpsProfile).filter(RelationshipOpsProfile.id == profile_id).first()

    @staticmethod
    def list_all(db: Session) -> List[RelationshipOpsProfile]:
        """List all relationship profiles."""
        return db.query(RelationshipOpsProfile).all()

    @staticmethod
    def update(db: Session, profile_id: int, data: RelationshipOpsProfileUpdate) -> Optional[RelationshipOpsProfile]:
        """Update a relationship profile."""
        profile = db.query(RelationshipOpsProfile).filter(RelationshipOpsProfile.id == profile_id).first()
        if not profile:
            return None
        
        if data.partner_name is not None:
            profile.partner_name = data.partner_name
        if data.shared_domains is not None:
            profile.shared_domains = [d.model_dump() for d in data.shared_domains]
        if data.communication_protocol is not None:
            profile.communication_protocol = [cp.model_dump() for cp in data.communication_protocol]
        if data.boundaries is not None:
            profile.boundaries = data.boundaries
        if data.notes is not None:
            profile.notes = data.notes
        profile.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def delete(db: Session, profile_id: int) -> bool:
        """Delete a relationship profile."""
        profile = db.query(RelationshipOpsProfile).filter(RelationshipOpsProfile.id == profile_id).first()
        if not profile:
            return False
        db.delete(profile)
        db.commit()
        return True


class CoParentingScheduleService:
    """Co-parenting schedule management."""

    @staticmethod
    def create(db: Session, data: CoParentingScheduleCreate) -> CoParentingSchedule:
        """Create a new schedule."""
        schedule = CoParentingSchedule(
            schedule_id=generate_id("schedule"),
            profile_id=data.profile_id,
            days=[d.model_dump() for d in data.days] if data.days else None,
            special_rules=data.special_rules,
            notes=data.notes
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        return schedule

    @staticmethod
    def get(db: Session, schedule_id: int) -> Optional[CoParentingSchedule]:
        """Get schedule by ID."""
        return db.query(CoParentingSchedule).filter(CoParentingSchedule.id == schedule_id).first()

    @staticmethod
    def get_by_profile(db: Session, profile_id: int) -> Optional[CoParentingSchedule]:
        """Get schedule for a profile."""
        return db.query(CoParentingSchedule).filter(CoParentingSchedule.profile_id == profile_id).first()

    @staticmethod
    def update(db: Session, schedule_id: int, data: CoParentingScheduleUpdate) -> Optional[CoParentingSchedule]:
        """Update a schedule."""
        schedule = db.query(CoParentingSchedule).filter(CoParentingSchedule.id == schedule_id).first()
        if not schedule:
            return None
        
        if data.days is not None:
            schedule.days = [d.model_dump() for d in data.days]
        if data.special_rules is not None:
            schedule.special_rules = data.special_rules
        if data.notes is not None:
            schedule.notes = data.notes
        schedule.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(schedule)
        return schedule

    @staticmethod
    def delete(db: Session, schedule_id: int) -> bool:
        """Delete a schedule."""
        schedule = db.query(CoParentingSchedule).filter(CoParentingSchedule.id == schedule_id).first()
        if not schedule:
            return False
        db.delete(schedule)
        db.commit()
        return True


class HouseholdResponsibilityService:
    """Household responsibility management."""

    @staticmethod
    def create(db: Session, data: HouseholdResponsibilityCreate) -> HouseholdResponsibility:
        """Create a new responsibility."""
        resp = HouseholdResponsibility(
            task_id=generate_id("task"),
            profile_id=data.profile_id,
            task=data.task,
            frequency=data.frequency,
            primary_responsible=data.primary_responsible,
            fallback_responsible=data.fallback_responsible,
            notes=data.notes
        )
        db.add(resp)
        db.commit()
        db.refresh(resp)
        return resp

    @staticmethod
    def get(db: Session, responsibility_id: int) -> Optional[HouseholdResponsibility]:
        """Get responsibility by ID."""
        return db.query(HouseholdResponsibility).filter(HouseholdResponsibility.id == responsibility_id).first()

    @staticmethod
    def list_by_profile(db: Session, profile_id: int) -> List[HouseholdResponsibility]:
        """List responsibilities for a profile."""
        return db.query(HouseholdResponsibility)\
            .filter(HouseholdResponsibility.profile_id == profile_id)\
            .all()

    @staticmethod
    def update(db: Session, responsibility_id: int, data: HouseholdResponsibilityUpdate) -> Optional[HouseholdResponsibility]:
        """Update a responsibility."""
        resp = db.query(HouseholdResponsibility).filter(HouseholdResponsibility.id == responsibility_id).first()
        if not resp:
            return None
        
        if data.task is not None:
            resp.task = data.task
        if data.frequency is not None:
            resp.frequency = data.frequency
        if data.primary_responsible is not None:
            resp.primary_responsible = data.primary_responsible
        if data.fallback_responsible is not None:
            resp.fallback_responsible = data.fallback_responsible
        if data.notes is not None:
            resp.notes = data.notes
        resp.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(resp)
        return resp

    @staticmethod
    def delete(db: Session, responsibility_id: int) -> bool:
        """Delete a responsibility."""
        resp = db.query(HouseholdResponsibility).filter(HouseholdResponsibility.id == responsibility_id).first()
        if not resp:
            return False
        db.delete(resp)
        db.commit()
        return True


class CommunicationLogService:
    """Communication log management."""

    @staticmethod
    def create(db: Session, data: CommunicationLogCreate) -> CommunicationLog:
        """Create a new log entry."""
        entry = CommunicationLog(
            log_id=generate_id("comlog"),
            profile_id=data.profile_id,
            date=data.date,
            topic=data.topic,
            summary=data.summary,
            follow_up_required=data.follow_up_required or False,
            notes=data.notes
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def get(db: Session, entry_id: int) -> Optional[CommunicationLog]:
        """Get log entry by ID."""
        return db.query(CommunicationLog).filter(CommunicationLog.id == entry_id).first()

    @staticmethod
    def list_by_profile(db: Session, profile_id: int, skip: int = 0, limit: int = 100) -> List[CommunicationLog]:
        """List entries for a profile."""
        return db.query(CommunicationLog)\
            .filter(CommunicationLog.profile_id == profile_id)\
            .order_by(CommunicationLog.date.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()


# ============================================================================
# PACK SO: Legacy & Succession Archive Services
# ============================================================================

class LegacyProfileService:
    """Legacy profile management."""

    @staticmethod
    def create(db: Session, data: LegacyProfileCreate) -> LegacyProfile:
        """Create a new legacy profile."""
        profile = LegacyProfile(
            legacy_id=generate_id("legacy"),
            description=data.description,
            long_term_goals=data.long_term_goals,
            knowledge_domains=[kd.model_dump() for kd in data.knowledge_domains] if data.knowledge_domains else None,
            heir_candidates=data.heir_candidates,
            notes=data.notes
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get(db: Session, profile_id: int) -> Optional[LegacyProfile]:
        """Get legacy profile by ID."""
        return db.query(LegacyProfile).filter(LegacyProfile.id == profile_id).first()

    @staticmethod
    def list_all(db: Session) -> List[LegacyProfile]:
        """List all legacy profiles."""
        return db.query(LegacyProfile).all()

    @staticmethod
    def update(db: Session, profile_id: int, data: LegacyProfileUpdate) -> Optional[LegacyProfile]:
        """Update a legacy profile."""
        profile = db.query(LegacyProfile).filter(LegacyProfile.id == profile_id).first()
        if not profile:
            return None
        
        if data.description is not None:
            profile.description = data.description
        if data.long_term_goals is not None:
            profile.long_term_goals = data.long_term_goals
        if data.knowledge_domains is not None:
            profile.knowledge_domains = [kd.model_dump() for kd in data.knowledge_domains]
        if data.heir_candidates is not None:
            profile.heir_candidates = data.heir_candidates
        if data.notes is not None:
            profile.notes = data.notes
        profile.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def delete(db: Session, profile_id: int) -> bool:
        """Delete a legacy profile."""
        profile = db.query(LegacyProfile).filter(LegacyProfile.id == profile_id).first()
        if not profile:
            return False
        db.delete(profile)
        db.commit()
        return True


class KnowledgePackageService:
    """Knowledge package management."""

    @staticmethod
    def create(db: Session, data: KnowledgePackageCreate) -> KnowledgePackage:
        """Create a new package."""
        package = KnowledgePackage(
            package_id=generate_id("package"),
            legacy_id=data.legacy_id,
            title=data.title,
            category=data.category,
            content=data.content,
            notes=data.notes
        )
        db.add(package)
        db.commit()
        db.refresh(package)
        return package

    @staticmethod
    def get(db: Session, package_id: int) -> Optional[KnowledgePackage]:
        """Get package by ID."""
        return db.query(KnowledgePackage).filter(KnowledgePackage.id == package_id).first()

    @staticmethod
    def list_by_legacy(db: Session, legacy_id: int) -> List[KnowledgePackage]:
        """List packages for a legacy."""
        return db.query(KnowledgePackage)\
            .filter(KnowledgePackage.legacy_id == legacy_id)\
            .all()

    @staticmethod
    def update(db: Session, package_id: int, data: KnowledgePackageUpdate) -> Optional[KnowledgePackage]:
        """Update a package."""
        package = db.query(KnowledgePackage).filter(KnowledgePackage.id == package_id).first()
        if not package:
            return None
        
        if data.title is not None:
            package.title = data.title
        if data.category is not None:
            package.category = data.category
        if data.content is not None:
            package.content = data.content
        if data.notes is not None:
            package.notes = data.notes
        package.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(package)
        return package

    @staticmethod
    def delete(db: Session, package_id: int) -> bool:
        """Delete a package."""
        package = db.query(KnowledgePackage).filter(KnowledgePackage.id == package_id).first()
        if not package:
            return False
        db.delete(package)
        db.commit()
        return True


class SuccessionStageService:
    """Succession stage management."""

    @staticmethod
    def create(db: Session, data: SuccessionStageCreate) -> SuccessionStage:
        """Create a new stage."""
        stage = SuccessionStage(
            stage_id=generate_id("stage"),
            legacy_id=data.legacy_id,
            description=data.description,
            trigger=data.trigger,
            access_level=[al.model_dump() for al in data.access_level] if data.access_level else None,
            training_requirements=data.training_requirements,
            notes=data.notes
        )
        db.add(stage)
        db.commit()
        db.refresh(stage)
        return stage

    @staticmethod
    def get(db: Session, stage_id: int) -> Optional[SuccessionStage]:
        """Get stage by ID."""
        return db.query(SuccessionStage).filter(SuccessionStage.id == stage_id).first()

    @staticmethod
    def list_by_legacy(db: Session, legacy_id: int) -> List[SuccessionStage]:
        """List stages for a legacy."""
        return db.query(SuccessionStage)\
            .filter(SuccessionStage.legacy_id == legacy_id)\
            .all()

    @staticmethod
    def update(db: Session, stage_id: int, data: SuccessionStageUpdate) -> Optional[SuccessionStage]:
        """Update a stage."""
        stage = db.query(SuccessionStage).filter(SuccessionStage.id == stage_id).first()
        if not stage:
            return None
        
        if data.description is not None:
            stage.description = data.description
        if data.trigger is not None:
            stage.trigger = data.trigger
        if data.access_level is not None:
            stage.access_level = [al.model_dump() for al in data.access_level]
        if data.training_requirements is not None:
            stage.training_requirements = data.training_requirements
        if data.notes is not None:
            stage.notes = data.notes
        stage.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(stage)
        return stage

    @staticmethod
    def delete(db: Session, stage_id: int) -> bool:
        """Delete a stage."""
        stage = db.query(SuccessionStage).filter(SuccessionStage.id == stage_id).first()
        if not stage:
            return False
        db.delete(stage)
        db.commit()
        return True


class LegacyVaultService:
    """Legacy vault management."""

    @staticmethod
    def create(db: Session, data: LegacyVaultCreate) -> LegacyVault:
        """Create a new vault."""
        vault = LegacyVault(
            vault_id=generate_id("vault"),
            legacy_id=data.legacy_id,
            packages=data.packages,
            successor_roles=data.successor_roles,
            notes=data.notes
        )
        db.add(vault)
        db.commit()
        db.refresh(vault)
        return vault

    @staticmethod
    def get(db: Session, vault_id: int) -> Optional[LegacyVault]:
        """Get vault by ID."""
        return db.query(LegacyVault).filter(LegacyVault.id == vault_id).first()

    @staticmethod
    def get_by_legacy(db: Session, legacy_id: int) -> Optional[LegacyVault]:
        """Get vault for a legacy."""
        return db.query(LegacyVault).filter(LegacyVault.legacy_id == legacy_id).first()

    @staticmethod
    def update(db: Session, vault_id: int, data: LegacyVaultUpdate) -> Optional[LegacyVault]:
        """Update a vault."""
        vault = db.query(LegacyVault).filter(LegacyVault.id == vault_id).first()
        if not vault:
            return None
        
        if data.packages is not None:
            vault.packages = data.packages
        if data.successor_roles is not None:
            vault.successor_roles = data.successor_roles
        if data.notes is not None:
            vault.notes = data.notes
        vault.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(vault)
        return vault

    @staticmethod
    def delete(db: Session, vault_id: int) -> bool:
        """Delete a vault."""
        vault = db.query(LegacyVault).filter(LegacyVault.id == vault_id).first()
        if not vault:
            return False
        db.delete(vault)
        db.commit()
        return True
