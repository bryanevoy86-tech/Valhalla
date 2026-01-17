"""
Test suite for PACK SP, SQ, SO

Comprehensive pytest tests for crisis management, relationship ops, and legacy/succession.
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.pack_sp import CrisisProfile, CrisisActionStep, CrisisLogEntry, CrisisWorkflow
from app.models.pack_sq import RelationshipOpsProfile, CoParentingSchedule, HouseholdResponsibility, CommunicationLog
from app.models.pack_so_legacy import LegacyProfile, KnowledgePackage, SuccessionStage, LegacyVault
from app.schemas.pack_sp_sq_so import (
    CrisisProfileCreate, CrisisActionStepCreate, CrisisLogEntryCreate, CrisisWorkflowCreate,
    RelationshipOpsProfileCreate, CoParentingScheduleCreate, HouseholdResponsibilityCreate, CommunicationLogCreate,
    LegacyProfileCreate, KnowledgePackageCreate, SuccessionStageCreate, LegacyVaultCreate
)
from app.services.pack_sp_sq_so import (
    CrisisProfileService, CrisisActionStepService, CrisisLogEntryService, CrisisWorkflowService,
    RelationshipOpsProfileService, CoParentingScheduleService, HouseholdResponsibilityService, CommunicationLogService,
    LegacyProfileService, KnowledgePackageService, SuccessionStageService, LegacyVaultService
)


# ============================================================================
# PACK SP: Crisis Management Tests
# ============================================================================

class TestCrisisProfileService:
    """Tests for CrisisProfileService."""

    def test_create_crisis_profile(self, db: Session):
        """Test creating a crisis profile."""
        data = CrisisProfileCreate(
            name="Family Conflict",
            category="family",
            triggers=["loud arguments", "prolonged silence"],
            notes="Protocol for handling family disputes"
        )
        profile = CrisisProfileService.create(db, data)
        
        assert profile.id is not None
        assert profile.crisis_id is not None
        assert profile.name == "Family Conflict"
        assert profile.category == "family"
        assert len(profile.triggers) == 2

    def test_get_crisis_profile(self, db: Session):
        """Test retrieving a crisis profile."""
        data = CrisisProfileCreate(name="Health Emergency", category="health")
        profile = CrisisProfileService.create(db, data)
        
        retrieved = CrisisProfileService.get(db, profile.id)
        assert retrieved is not None
        assert retrieved.id == profile.id
        assert retrieved.name == "Health Emergency"

    def test_list_crisis_profiles(self, db: Session):
        """Test listing crisis profiles."""
        for i in range(3):
            data = CrisisProfileCreate(name=f"Crisis {i}", category="financial")
            CrisisProfileService.create(db, data)
        
        profiles = CrisisProfileService.list_all(db)
        assert len(profiles) >= 3

    def test_update_crisis_profile(self, db: Session):
        """Test updating a crisis profile."""
        data = CrisisProfileCreate(name="Original", category="legal")
        profile = CrisisProfileService.create(db, data)
        
        from app.schemas.pack_sp_sq_so import CrisisProfileUpdate
        update = CrisisProfileUpdate(name="Updated", notes="New notes")
        updated = CrisisProfileService.update(db, profile.id, update)
        
        assert updated.name == "Updated"
        assert updated.notes == "New notes"

    def test_delete_crisis_profile(self, db: Session):
        """Test deleting a crisis profile."""
        data = CrisisProfileCreate(name="To Delete", category="operations")
        profile = CrisisProfileService.create(db, data)
        
        deleted = CrisisProfileService.delete(db, profile.id)
        assert deleted is True
        
        retrieved = CrisisProfileService.get(db, profile.id)
        assert retrieved is None


class TestCrisisActionStepService:
    """Tests for CrisisActionStepService."""

    def test_create_action_step(self, db: Session):
        """Test creating an action step."""
        profile = CrisisProfileService.create(db, CrisisProfileCreate(name="Test", category="family"))
        
        data = CrisisActionStepCreate(
            crisis_id=profile.id,
            order=1,
            action="Contact lawyer",
            responsible_role="King"
        )
        step = CrisisActionStepService.create(db, data)
        
        assert step.id is not None
        assert step.step_id is not None
        assert step.action == "Contact lawyer"
        assert step.responsible_role == "King"

    def test_list_crisis_steps(self, db: Session):
        """Test listing steps for a crisis."""
        profile = CrisisProfileService.create(db, CrisisProfileCreate(name="Test", category="family"))
        
        for i in range(3):
            data = CrisisActionStepCreate(
                crisis_id=profile.id,
                order=i+1,
                action=f"Step {i+1}",
                responsible_role="Queen"
            )
            CrisisActionStepService.create(db, data)
        
        steps = CrisisActionStepService.list_by_crisis(db, profile.id)
        assert len(steps) == 3
        assert steps[0].order == 1


class TestCrisisLogEntryService:
    """Tests for CrisisLogEntryService."""

    def test_create_log_entry(self, db: Session):
        """Test creating a log entry."""
        profile = CrisisProfileService.create(db, CrisisProfileCreate(name="Test", category="family"))
        
        data = CrisisLogEntryCreate(
            crisis_id=profile.id,
            date=datetime.utcnow(),
            event="Argument occurred",
            actions_taken=["Called counselor", "Scheduled meeting"],
            status="active"
        )
        entry = CrisisLogEntryService.create(db, data)
        
        assert entry.id is not None
        assert entry.log_id is not None
        assert entry.event == "Argument occurred"
        assert entry.status == "active"


class TestCrisisWorkflowService:
    """Tests for CrisisWorkflowService."""

    def test_create_workflow(self, db: Session):
        """Test creating a workflow."""
        data = CrisisWorkflowCreate(
            crisis_id="crisis-123",
            status="intake",
            triggered_date=datetime.utcnow()
        )
        workflow = CrisisWorkflowService.create(db, data)
        
        assert workflow.id is not None
        assert workflow.workflow_id is not None
        assert workflow.status == "intake"
        assert workflow.steps_completed == 0


# ============================================================================
# PACK SQ: Partner/Marriage Stability Ops Tests
# ============================================================================

class TestRelationshipOpsProfileService:
    """Tests for RelationshipOpsProfileService."""

    def test_create_relationship_profile(self, db: Session):
        """Test creating a relationship ops profile."""
        from app.schemas.pack_sp_sq_so import SharedDomain
        
        data = RelationshipOpsProfileCreate(
            partner_name="Jane Doe",
            shared_domains=[
                SharedDomain(domain="parenting", primary_responsible="Both", secondary_responsible="Alternating")
            ],
            boundaries=["No work discussions at dinner", "Respectful tone always"]
        )
        profile = RelationshipOpsProfileService.create(db, data)
        
        assert profile.id is not None
        assert profile.profile_id is not None
        assert profile.partner_name == "Jane Doe"
        assert len(profile.boundaries) == 2

    def test_get_relationship_profile(self, db: Session):
        """Test retrieving a relationship profile."""
        data = RelationshipOpsProfileCreate(partner_name="Partner Name")
        profile = RelationshipOpsProfileService.create(db, data)
        
        retrieved = RelationshipOpsProfileService.get(db, profile.id)
        assert retrieved is not None
        assert retrieved.partner_name == "Partner Name"


class TestCoParentingScheduleService:
    """Tests for CoParentingScheduleService."""

    def test_create_schedule(self, db: Session):
        """Test creating a co-parenting schedule."""
        profile = RelationshipOpsProfileService.create(db, RelationshipOpsProfileCreate(partner_name="Partner"))
        
        from app.schemas.pack_sp_sq_so import CoParentingDay
        data = CoParentingScheduleCreate(
            profile_id=profile.id,
            days=[
                CoParentingDay(day="Monday", responsible_parent="Parent A", pickup_time="3:00 PM"),
                CoParentingDay(day="Tuesday", responsible_parent="Parent B", pickup_time="3:30 PM")
            ]
        )
        schedule = CoParentingScheduleService.create(db, data)
        
        assert schedule.id is not None
        assert schedule.schedule_id is not None
        assert len(schedule.days) == 2


class TestHouseholdResponsibilityService:
    """Tests for HouseholdResponsibilityService."""

    def test_create_responsibility(self, db: Session):
        """Test creating a household responsibility."""
        profile = RelationshipOpsProfileService.create(db, RelationshipOpsProfileCreate(partner_name="Partner"))
        
        data = HouseholdResponsibilityCreate(
            profile_id=profile.id,
            task="Grocery shopping",
            frequency="weekly",
            primary_responsible="Parent A",
            fallback_responsible="Parent B"
        )
        resp = HouseholdResponsibilityService.create(db, data)
        
        assert resp.id is not None
        assert resp.task_id is not None
        assert resp.task == "Grocery shopping"
        assert resp.frequency == "weekly"

    def test_list_responsibilities(self, db: Session):
        """Test listing responsibilities for a profile."""
        profile = RelationshipOpsProfileService.create(db, RelationshipOpsProfileCreate(partner_name="Partner"))
        
        for i in range(2):
            data = HouseholdResponsibilityCreate(
                profile_id=profile.id,
                task=f"Task {i+1}",
                frequency="daily",
                primary_responsible="A"
            )
            HouseholdResponsibilityService.create(db, data)
        
        resps = HouseholdResponsibilityService.list_by_profile(db, profile.id)
        assert len(resps) == 2


class TestCommunicationLogService:
    """Tests for CommunicationLogService."""

    def test_create_communication_log(self, db: Session):
        """Test creating a communication log."""
        profile = RelationshipOpsProfileService.create(db, RelationshipOpsProfileCreate(partner_name="Partner"))
        
        data = CommunicationLogCreate(
            profile_id=profile.id,
            date=datetime.utcnow(),
            topic="Weekly planning",
            summary="Discussed schedule for next week",
            follow_up_required=True
        )
        entry = CommunicationLogService.create(db, data)
        
        assert entry.id is not None
        assert entry.log_id is not None
        assert entry.topic == "Weekly planning"
        assert entry.follow_up_required is True


# ============================================================================
# PACK SO: Legacy & Succession Archive Tests
# ============================================================================

class TestLegacyProfileService:
    """Tests for LegacyProfileService."""

    def test_create_legacy_profile(self, db: Session):
        """Test creating a legacy profile."""
        from app.schemas.pack_sp_sq_so import KnowledgeDomain
        
        data = LegacyProfileCreate(
            description="Family business succession",
            long_term_goals=["Ensure continuity", "Develop next generation"],
            knowledge_domains=[
                KnowledgeDomain(domain="Finance", description="Business finances")
            ],
            heir_candidates=["Child A", "Child B"]
        )
        profile = LegacyProfileService.create(db, data)
        
        assert profile.id is not None
        assert profile.legacy_id is not None
        assert len(profile.heir_candidates) == 2

    def test_get_legacy_profile(self, db: Session):
        """Test retrieving a legacy profile."""
        data = LegacyProfileCreate(description="My Legacy")
        profile = LegacyProfileService.create(db, data)
        
        retrieved = LegacyProfileService.get(db, profile.id)
        assert retrieved is not None
        assert retrieved.description == "My Legacy"


class TestKnowledgePackageService:
    """Tests for KnowledgePackageService."""

    def test_create_package(self, db: Session):
        """Test creating a knowledge package."""
        legacy = LegacyProfileService.create(db, LegacyProfileCreate(description="Test"))
        
        data = KnowledgePackageCreate(
            legacy_id=legacy.id,
            title="Financial Management",
            category="finance",
            content="How to manage the family finances..."
        )
        package = KnowledgePackageService.create(db, data)
        
        assert package.id is not None
        assert package.package_id is not None
        assert package.title == "Financial Management"
        assert package.category == "finance"

    def test_list_packages(self, db: Session):
        """Test listing packages for a legacy."""
        legacy = LegacyProfileService.create(db, LegacyProfileCreate(description="Test"))
        
        for i in range(2):
            data = KnowledgePackageCreate(
                legacy_id=legacy.id,
                title=f"Package {i+1}",
                category="finance",
                content=f"Content {i+1}"
            )
            KnowledgePackageService.create(db, data)
        
        packages = KnowledgePackageService.list_by_legacy(db, legacy.id)
        assert len(packages) == 2


class TestSuccessionStageService:
    """Tests for SuccessionStageService."""

    def test_create_succession_stage(self, db: Session):
        """Test creating a succession stage."""
        from app.schemas.pack_sp_sq_so import AccessLevel
        
        legacy = LegacyProfileService.create(db, LegacyProfileCreate(description="Test"))
        
        data = SuccessionStageCreate(
            legacy_id=legacy.id,
            description="Age 14 milestone",
            trigger="age 14",
            access_level=[
                AccessLevel(module="finances", level="read-only")
            ],
            training_requirements=["Financial literacy course"]
        )
        stage = SuccessionStageService.create(db, data)
        
        assert stage.id is not None
        assert stage.stage_id is not None
        assert stage.trigger == "age 14"
        assert len(stage.access_level) == 1


class TestLegacyVaultService:
    """Tests for LegacyVaultService."""

    def test_create_vault(self, db: Session):
        """Test creating a legacy vault."""
        legacy = LegacyProfileService.create(db, LegacyProfileCreate(description="Test"))
        
        data = LegacyVaultCreate(
            legacy_id=legacy.id,
            packages=["pkg-1", "pkg-2"],
            successor_roles=["Primary Heir", "Secondary Heir"]
        )
        vault = LegacyVaultService.create(db, data)
        
        assert vault.id is not None
        assert vault.vault_id is not None
        assert len(vault.packages) == 2

    def test_get_vault_by_legacy(self, db: Session):
        """Test retrieving vault for a legacy."""
        legacy = LegacyProfileService.create(db, LegacyProfileCreate(description="Test"))
        
        data = LegacyVaultCreate(legacy_id=legacy.id)
        vault = LegacyVaultService.create(db, data)
        
        retrieved = LegacyVaultService.get_by_legacy(db, legacy.id)
        assert retrieved is not None
        assert retrieved.vault_id == vault.vault_id
