"""
Comprehensive test suite for PACK SZ, TA, TB

Tests for philosophy, relationships, and daily rhythm functionality.
"""

import pytest
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.models.pack_sz import PhilosophyRecord, EmpirePrinciple, PhilosophySnapshot
from app.models.pack_ta import RelationshipProfile, TrustEventLog, RelationshipMapSnapshot
from app.models.pack_tb import DailyRhythmProfile, TempoRule, DailyTempoSnapshot
from app.services.pack_sz_ta_tb import (
    PhilosophyRecordService, EmpirePrincipleService, PhilosophySnapshotService,
    RelationshipProfileService, TrustEventLogService, RelationshipMapSnapshotService,
    DailyRhythmProfileService, TempoRuleService, DailyTempoSnapshotService
)
from app.schemas.pack_sz_ta_tb import (
    PhilosophyRecordCreate, PhilosophyRecordUpdate,
    EmpirePrincipleCreate, EmpirePrincipleUpdate,
    PhilosophySnapshotCreate, PhilosophySnapshotUpdate,
    RelationshipProfileCreate, RelationshipProfileUpdate,
    TrustEventLogCreate, TrustEventLogUpdate,
    RelationshipMapSnapshotCreate, RelationshipMapSnapshotUpdate,
    DailyRhythmProfileCreate, DailyRhythmProfileUpdate,
    TempoRuleCreate, TempoRuleUpdate,
    DailyTempoSnapshotCreate, DailyTempoSnapshotUpdate,
    TimeBlock
)


# =============================================================================
# PACK SZ Tests: Philosophy
# =============================================================================

class TestPhilosophyRecordService:
    """Test philosophy record service."""

    def test_create_philosophy_record(self, db: Session):
        """Test creating a philosophy record."""
        data = PhilosophyRecordCreate(
            title="Core Life Philosophy",
            date=date.today(),
            pillars=["Family", "Growth", "Impact"],
            mission_statement="Build systems that align with values",
            values=["Integrity", "Persistence", "Learning"],
            rules_to_follow=["Be honest", "Keep promises", "Learn daily"],
            rules_to_never_break=["Never deceive", "Never harm family"],
            long_term_intent="Create lasting positive impact",
            notes="Foundation of all decisions"
        )
        result = PhilosophyRecordService.create(db, data)
        assert result.id is not None
        assert result.title == "Core Life Philosophy"
        assert len(result.pillars) == 3
        assert result.record_id.startswith("phil-")

    def test_get_philosophy_record(self, db: Session):
        """Test retrieving a philosophy record."""
        data = PhilosophyRecordCreate(
            title="Test Philosophy", date=date.today(), pillars=["Test"],
            mission_statement="Test", values=[], rules_to_follow=[],
            rules_to_never_break=[], long_term_intent="Test", notes=""
        )
        created = PhilosophyRecordService.create(db, data)
        retrieved = PhilosophyRecordService.get(db, created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Test Philosophy"

    def test_list_philosophy_records(self, db: Session):
        """Test listing philosophy records."""
        for i in range(3):
            data = PhilosophyRecordCreate(
                title=f"Philosophy {i}", date=date.today(), pillars=["Test"],
                mission_statement="Test", values=[], rules_to_follow=[],
                rules_to_never_break=[], long_term_intent="Test", notes=""
            )
            PhilosophyRecordService.create(db, data)
        
        records = PhilosophyRecordService.list_all(db)
        assert len(records) >= 3

    def test_update_philosophy_record(self, db: Session):
        """Test updating a philosophy record."""
        data = PhilosophyRecordCreate(
            title="Original", date=date.today(), pillars=["Test"],
            mission_statement="Test", values=[], rules_to_follow=[],
            rules_to_never_break=[], long_term_intent="Test", notes=""
        )
        created = PhilosophyRecordService.create(db, data)
        
        update_data = PhilosophyRecordUpdate(
            title="Updated",
            values=["New Value"]
        )
        updated = PhilosophyRecordService.update(db, created.id, update_data)
        assert updated.title == "Updated"
        assert "New Value" in updated.values

    def test_delete_philosophy_record(self, db: Session):
        """Test deleting a philosophy record."""
        data = PhilosophyRecordCreate(
            title="To Delete", date=date.today(), pillars=["Test"],
            mission_statement="Test", values=[], rules_to_follow=[],
            rules_to_never_break=[], long_term_intent="Test", notes=""
        )
        created = PhilosophyRecordService.create(db, data)
        
        assert PhilosophyRecordService.delete(db, created.id)
        assert PhilosophyRecordService.get(db, created.id) is None


class TestEmpirePrincipleService:
    """Test empire principle service."""

    def test_create_empire_principle(self, db: Session, philosophy_record):
        """Test creating an empire principle."""
        data = EmpirePrincipleCreate(
            record_id=philosophy_record.id,
            category="ethics",
            description="Always act with integrity",
            enforcement_level="strong",
            notes="Core ethical principle"
        )
        result = EmpirePrincipleService.create(db, data)
        assert result.id is not None
        assert result.principle_id.startswith("prin-")
        assert result.category == "ethics"

    def test_list_principles_by_record(self, db: Session, philosophy_record):
        """Test listing principles by record."""
        for i, category in enumerate(["ethics", "growth", "family"]):
            data = EmpirePrincipleCreate(
                record_id=philosophy_record.id,
                category=category,
                description=f"Principle {i}",
                enforcement_level="soft",
                notes=""
            )
            EmpirePrincipleService.create(db, data)
        
        principles = EmpirePrincipleService.list_by_record(db, philosophy_record.id)
        assert len(principles) >= 3

    def test_list_principles_by_category(self, db: Session, philosophy_record):
        """Test listing principles by category."""
        for _ in range(2):
            data = EmpirePrincipleCreate(
                record_id=philosophy_record.id,
                category="ethics",
                description="Test principle",
                enforcement_level="soft",
                notes=""
            )
            EmpirePrincipleService.create(db, data)
        
        principles = EmpirePrincipleService.list_by_category(db, "ethics")
        assert len(principles) >= 2

    def test_update_empire_principle(self, db: Session, philosophy_record):
        """Test updating an empire principle."""
        data = EmpirePrincipleCreate(
            record_id=philosophy_record.id,
            category="ethics",
            description="Original",
            enforcement_level="soft",
            notes=""
        )
        created = EmpirePrincipleService.create(db, data)
        
        update_data = EmpirePrincipleUpdate(
            description="Updated",
            enforcement_level="strong"
        )
        updated = EmpirePrincipleService.update(db, created.id, update_data)
        assert updated.description == "Updated"
        assert updated.enforcement_level == "strong"

    def test_delete_empire_principle(self, db: Session, philosophy_record):
        """Test deleting an empire principle."""
        data = EmpirePrincipleCreate(
            record_id=philosophy_record.id,
            category="ethics",
            description="To delete",
            enforcement_level="soft",
            notes=""
        )
        created = EmpirePrincipleService.create(db, data)
        
        assert EmpirePrincipleService.delete(db, created.id)
        assert EmpirePrincipleService.get(db, created.id) is None


class TestPhilosophySnapshotService:
    """Test philosophy snapshot service."""

    def test_create_philosophy_snapshot(self, db: Session):
        """Test creating a philosophy snapshot."""
        data = PhilosophySnapshotCreate(
            date=date.today(),
            core_pillars=["Family", "Growth"],
            recent_updates=["Added new principle"],
            impact_on_system=["Improved decision-making"],
            user_notes="Snapshot of current state"
        )
        result = PhilosophySnapshotService.create(db, data)
        assert result.id is not None
        assert result.snapshot_id.startswith("philsnap-")

    def test_get_philosophy_snapshot(self, db: Session):
        """Test retrieving a philosophy snapshot."""
        data = PhilosophySnapshotCreate(
            date=date.today(),
            core_pillars=["Test"],
            recent_updates=[],
            impact_on_system=[],
            user_notes=""
        )
        created = PhilosophySnapshotService.create(db, data)
        retrieved = PhilosophySnapshotService.get(db, created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_list_philosophy_snapshots(self, db: Session):
        """Test listing philosophy snapshots."""
        for i in range(3):
            data = PhilosophySnapshotCreate(
                date=date.today(),
                core_pillars=["Test"],
                recent_updates=[],
                impact_on_system=[],
                user_notes=f"Snapshot {i}"
            )
            PhilosophySnapshotService.create(db, data)
        
        snapshots = PhilosophySnapshotService.list_all(db)
        assert len(snapshots) >= 3

    def test_update_philosophy_snapshot(self, db: Session):
        """Test updating a philosophy snapshot."""
        data = PhilosophySnapshotCreate(
            date=date.today(),
            core_pillars=["Original"],
            recent_updates=[],
            impact_on_system=[],
            user_notes=""
        )
        created = PhilosophySnapshotService.create(db, data)
        
        update_data = PhilosophySnapshotUpdate(
            core_pillars=["Updated"],
            user_notes="Updated snapshot"
        )
        updated = PhilosophySnapshotService.update(db, created.id, update_data)
        assert "Updated" in updated.core_pillars


# =============================================================================
# PACK TA Tests: Relationships & Trust
# =============================================================================

class TestRelationshipProfileService:
    """Test relationship profile service."""

    def test_create_relationship_profile(self, db: Session):
        """Test creating a relationship profile."""
        data = RelationshipProfileCreate(
            name="John Doe",
            role="mentor",
            relationship_type="supportive",
            user_defined_trust_level=8,
            boundaries=["No personal finance discussions"],
            notes="Long-time mentor and friend"
        )
        result = RelationshipProfileService.create(db, data)
        assert result.id is not None
        assert result.profile_id.startswith("relprof-")
        assert result.name == "John Doe"
        assert result.user_defined_trust_level == 8

    def test_get_relationship_profile(self, db: Session):
        """Test retrieving a relationship profile."""
        data = RelationshipProfileCreate(
            name="Jane Doe",
            role="colleague",
            relationship_type="professional",
            user_defined_trust_level=6,
            boundaries=[],
            notes=""
        )
        created = RelationshipProfileService.create(db, data)
        retrieved = RelationshipProfileService.get(db, created.id)
        assert retrieved is not None
        assert retrieved.name == "Jane Doe"

    def test_list_relationship_profiles(self, db: Session):
        """Test listing relationship profiles."""
        for i in range(3):
            data = RelationshipProfileCreate(
                name=f"Person {i}",
                role="test",
                relationship_type="professional",
                user_defined_trust_level=5,
                boundaries=[],
                notes=""
            )
            RelationshipProfileService.create(db, data)
        
        profiles = RelationshipProfileService.list_all(db)
        assert len(profiles) >= 3

    def test_list_profiles_by_role(self, db: Session):
        """Test listing profiles by role."""
        for _ in range(2):
            data = RelationshipProfileCreate(
                name="Test Person",
                role="mentor",
                relationship_type="supportive",
                user_defined_trust_level=7,
                boundaries=[],
                notes=""
            )
            RelationshipProfileService.create(db, data)
        
        profiles = RelationshipProfileService.list_by_role(db, "mentor")
        assert len(profiles) >= 2

    def test_update_relationship_profile(self, db: Session):
        """Test updating a relationship profile."""
        data = RelationshipProfileCreate(
            name="Test Person",
            role="friend",
            relationship_type="supportive",
            user_defined_trust_level=7,
            boundaries=["Old boundary"],
            notes="Original"
        )
        created = RelationshipProfileService.create(db, data)
        
        update_data = RelationshipProfileUpdate(
            user_defined_trust_level=9,
            boundaries=["New boundary"],
            notes="Updated"
        )
        updated = RelationshipProfileService.update(db, created.id, update_data)
        assert updated.user_defined_trust_level == 9
        assert "New boundary" in updated.boundaries

    def test_delete_relationship_profile(self, db: Session):
        """Test deleting a relationship profile."""
        data = RelationshipProfileCreate(
            name="To Delete",
            role="test",
            relationship_type="professional",
            user_defined_trust_level=5,
            boundaries=[],
            notes=""
        )
        created = RelationshipProfileService.create(db, data)
        
        assert RelationshipProfileService.delete(db, created.id)
        assert RelationshipProfileService.get(db, created.id) is None


class TestTrustEventLogService:
    """Test trust event log service."""

    def test_create_trust_event(self, db: Session, relationship_profile):
        """Test creating a trust event."""
        data = TrustEventLogCreate(
            profile_id=relationship_profile.id,
            date=date.today(),
            event_description="Provided valuable advice",
            trust_change=3,
            notes="Increased trust due to helpful guidance"
        )
        result = TrustEventLogService.create(db, data)
        assert result.id is not None
        assert result.event_id.startswith("trustevent-")
        assert result.trust_change == 3

    def test_list_events_by_profile(self, db: Session, relationship_profile):
        """Test listing trust events by profile."""
        for i in range(3):
            data = TrustEventLogCreate(
                profile_id=relationship_profile.id,
                date=date.today(),
                event_description=f"Event {i}",
                trust_change=1,
                notes=""
            )
            TrustEventLogService.create(db, data)
        
        events = TrustEventLogService.list_by_profile(db, relationship_profile.id)
        assert len(events) >= 3

    def test_update_trust_event(self, db: Session, relationship_profile):
        """Test updating a trust event."""
        data = TrustEventLogCreate(
            profile_id=relationship_profile.id,
            date=date.today(),
            event_description="Original event",
            trust_change=2,
            notes="Original notes"
        )
        created = TrustEventLogService.create(db, data)
        
        update_data = TrustEventLogUpdate(
            trust_change=5,
            notes="Updated notes"
        )
        updated = TrustEventLogService.update(db, created.id, update_data)
        assert updated.trust_change == 5
        assert updated.notes == "Updated notes"

    def test_cascade_delete_on_profile_delete(self, db: Session):
        """Test that trust events cascade delete when profile is deleted."""
        profile_data = RelationshipProfileCreate(
            name="Test Person",
            role="test",
            relationship_type="professional",
            user_defined_trust_level=5,
            boundaries=[],
            notes=""
        )
        profile = RelationshipProfileService.create(db, profile_data)
        
        event_data = TrustEventLogCreate(
            profile_id=profile.id,
            date=date.today(),
            event_description="Test event",
            trust_change=1,
            notes=""
        )
        event = TrustEventLogService.create(db, event_data)
        
        RelationshipProfileService.delete(db, profile.id)
        assert TrustEventLogService.get(db, event.id) is None


class TestRelationshipMapSnapshotService:
    """Test relationship map snapshot service."""

    def test_create_relationship_snapshot(self, db: Session):
        """Test creating a relationship map snapshot."""
        data = RelationshipMapSnapshotCreate(
            date=date.today(),
            key_people=["John", "Jane", "Bob"],
            trust_levels={"John": 8, "Jane": 6, "Bob": 5},
            boundaries={"John": ["Finance"], "Jane": [], "Bob": ["Personal"]},
            notes="Current relationship map"
        )
        result = RelationshipMapSnapshotService.create(db, data)
        assert result.id is not None
        assert result.snapshot_id.startswith("relsnap-")
        assert len(result.key_people) == 3

    def test_get_relationship_snapshot(self, db: Session):
        """Test retrieving a relationship snapshot."""
        data = RelationshipMapSnapshotCreate(
            date=date.today(),
            key_people=["Test"],
            trust_levels={"Test": 5},
            boundaries={},
            notes=""
        )
        created = RelationshipMapSnapshotService.create(db, data)
        retrieved = RelationshipMapSnapshotService.get(db, created.id)
        assert retrieved is not None
        assert "Test" in retrieved.key_people

    def test_list_relationship_snapshots(self, db: Session):
        """Test listing relationship snapshots."""
        for i in range(3):
            data = RelationshipMapSnapshotCreate(
                date=date.today(),
                key_people=[f"Person {i}"],
                trust_levels={},
                boundaries={},
                notes=""
            )
            RelationshipMapSnapshotService.create(db, data)
        
        snapshots = RelationshipMapSnapshotService.list_all(db)
        assert len(snapshots) >= 3


# =============================================================================
# PACK TB Tests: Daily Rhythm & Tempo
# =============================================================================

class TestDailyRhythmProfileService:
    """Test daily rhythm profile service."""

    def test_create_daily_rhythm_profile(self, db: Session):
        """Test creating a daily rhythm profile."""
        time_blocks = [TimeBlock(start="06:00", end="08:00"), TimeBlock(start="20:00", end="22:00")]
        data = DailyRhythmProfileCreate(
            wake_time="06:00",
            sleep_time="23:00",
            peak_focus_blocks=time_blocks,
            low_energy_blocks=[TimeBlock(start="14:00", end="16:00")],
            family_blocks=[TimeBlock(start="18:00", end="19:00")],
            personal_time_blocks=[TimeBlock(start="19:00", end="20:00")],
            notes="Standard daily routine"
        )
        result = DailyRhythmProfileService.create(db, data)
        assert result.id is not None
        assert result.profile_id.startswith("rhythm-")
        assert result.wake_time == "06:00"

    def test_get_daily_rhythm_profile(self, db: Session):
        """Test retrieving a daily rhythm profile."""
        time_blocks = [TimeBlock(start="06:00", end="08:00")]
        data = DailyRhythmProfileCreate(
            wake_time="06:00",
            sleep_time="23:00",
            peak_focus_blocks=time_blocks,
            low_energy_blocks=[],
            family_blocks=[],
            personal_time_blocks=[],
            notes=""
        )
        created = DailyRhythmProfileService.create(db, data)
        retrieved = DailyRhythmProfileService.get(db, created.id)
        assert retrieved is not None
        assert retrieved.wake_time == "06:00"

    def test_list_daily_rhythm_profiles(self, db: Session):
        """Test listing daily rhythm profiles."""
        for i in range(3):
            time_blocks = [TimeBlock(start="06:00", end="08:00")]
            data = DailyRhythmProfileCreate(
                wake_time="06:00",
                sleep_time="23:00",
                peak_focus_blocks=time_blocks,
                low_energy_blocks=[],
                family_blocks=[],
                personal_time_blocks=[],
                notes=f"Profile {i}"
            )
            DailyRhythmProfileService.create(db, data)
        
        profiles = DailyRhythmProfileService.list_all(db)
        assert len(profiles) >= 3

    def test_update_daily_rhythm_profile(self, db: Session):
        """Test updating a daily rhythm profile."""
        time_blocks = [TimeBlock(start="06:00", end="08:00")]
        data = DailyRhythmProfileCreate(
            wake_time="06:00",
            sleep_time="23:00",
            peak_focus_blocks=time_blocks,
            low_energy_blocks=[],
            family_blocks=[],
            personal_time_blocks=[],
            notes="Original"
        )
        created = DailyRhythmProfileService.create(db, data)
        
        update_data = DailyRhythmProfileUpdate(
            wake_time="05:30",
            notes="Updated"
        )
        updated = DailyRhythmProfileService.update(db, created.id, update_data)
        assert updated.wake_time == "05:30"


class TestTempoRuleService:
    """Test tempo rule service."""

    def test_create_tempo_rule(self, db: Session, daily_rhythm_profile):
        """Test creating a tempo rule."""
        data = TempoRuleCreate(
            profile_id=daily_rhythm_profile.id,
            time_block="morning",
            action_intensity="push",
            communication_style="short",
            notes="Maximize morning productivity"
        )
        result = TempoRuleService.create(db, data)
        assert result.id is not None
        assert result.rule_id.startswith("tempo-")
        assert result.action_intensity == "push"

    def test_list_rules_by_profile(self, db: Session, daily_rhythm_profile):
        """Test listing tempo rules by profile."""
        for time_block in ["morning", "afternoon", "evening"]:
            data = TempoRuleCreate(
                profile_id=daily_rhythm_profile.id,
                time_block=time_block,
                action_intensity="balanced",
                communication_style="check_in",
                notes=""
            )
            TempoRuleService.create(db, data)
        
        rules = TempoRuleService.list_by_profile(db, daily_rhythm_profile.id)
        assert len(rules) >= 3

    def test_update_tempo_rule(self, db: Session, daily_rhythm_profile):
        """Test updating a tempo rule."""
        data = TempoRuleCreate(
            profile_id=daily_rhythm_profile.id,
            time_block="morning",
            action_intensity="push",
            communication_style="short",
            notes="Original"
        )
        created = TempoRuleService.create(db, data)
        
        update_data = TempoRuleUpdate(
            action_intensity="gentle",
            notes="Updated"
        )
        updated = TempoRuleService.update(db, created.id, update_data)
        assert updated.action_intensity == "gentle"

    def test_cascade_delete_on_profile_delete(self, db: Session):
        """Test that tempo rules cascade delete when profile is deleted."""
        time_blocks = [TimeBlock(start="06:00", end="08:00")]
        profile_data = DailyRhythmProfileCreate(
            wake_time="06:00",
            sleep_time="23:00",
            peak_focus_blocks=time_blocks,
            low_energy_blocks=[],
            family_blocks=[],
            personal_time_blocks=[],
            notes=""
        )
        profile = DailyRhythmProfileService.create(db, profile_data)
        
        rule_data = TempoRuleCreate(
            profile_id=profile.id,
            time_block="morning",
            action_intensity="push",
            communication_style="short",
            notes=""
        )
        rule = TempoRuleService.create(db, rule_data)
        
        DailyRhythmProfileService.delete(db, profile.id)
        assert TempoRuleService.get(db, rule.id) is None


class TestDailyTempoSnapshotService:
    """Test daily tempo snapshot service."""

    def test_create_daily_tempo_snapshot(self, db: Session):
        """Test creating a daily tempo snapshot."""
        data = DailyTempoSnapshotCreate(
            date=date.today(),
            rhythm_followed=True,
            adjustments_needed=["Extend morning focus block"],
            user_notes="Good rhythm day"
        )
        result = DailyTempoSnapshotService.create(db, data)
        assert result.id is not None
        assert result.snapshot_id.startswith("daytemp-")
        assert result.rhythm_followed is True

    def test_get_daily_tempo_snapshot(self, db: Session):
        """Test retrieving a daily tempo snapshot."""
        data = DailyTempoSnapshotCreate(
            date=date.today(),
            rhythm_followed=False,
            adjustments_needed=[],
            user_notes=""
        )
        created = DailyTempoSnapshotService.create(db, data)
        retrieved = DailyTempoSnapshotService.get(db, created.id)
        assert retrieved is not None
        assert retrieved.rhythm_followed is False

    def test_list_daily_tempo_snapshots(self, db: Session):
        """Test listing daily tempo snapshots."""
        for i in range(3):
            data = DailyTempoSnapshotCreate(
                date=date.today(),
                rhythm_followed=(i % 2 == 0),
                adjustments_needed=[],
                user_notes=f"Snapshot {i}"
            )
            DailyTempoSnapshotService.create(db, data)
        
        snapshots = DailyTempoSnapshotService.list_all(db)
        assert len(snapshots) >= 3

    def test_update_daily_tempo_snapshot(self, db: Session):
        """Test updating a daily tempo snapshot."""
        data = DailyTempoSnapshotCreate(
            date=date.today(),
            rhythm_followed=False,
            adjustments_needed=[],
            user_notes="Original"
        )
        created = DailyTempoSnapshotService.create(db, data)
        
        update_data = DailyTempoSnapshotUpdate(
            rhythm_followed=True,
            adjustments_needed=["Adjust evening routine"],
            user_notes="Updated"
        )
        updated = DailyTempoSnapshotService.update(db, created.id, update_data)
        assert updated.rhythm_followed is True


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def philosophy_record(db: Session):
    """Create a test philosophy record."""
    data = PhilosophyRecordCreate(
        title="Test Philosophy",
        date=date.today(),
        pillars=["Test"],
        mission_statement="Test",
        values=[],
        rules_to_follow=[],
        rules_to_never_break=[],
        long_term_intent="Test",
        notes=""
    )
    return PhilosophyRecordService.create(db, data)


@pytest.fixture
def relationship_profile(db: Session):
    """Create a test relationship profile."""
    data = RelationshipProfileCreate(
        name="Test Person",
        role="test",
        relationship_type="professional",
        user_defined_trust_level=5,
        boundaries=[],
        notes=""
    )
    return RelationshipProfileService.create(db, data)


@pytest.fixture
def daily_rhythm_profile(db: Session):
    """Create a test daily rhythm profile."""
    time_blocks = [TimeBlock(start="06:00", end="08:00")]
    data = DailyRhythmProfileCreate(
        wake_time="06:00",
        sleep_time="23:00",
        peak_focus_blocks=time_blocks,
        low_energy_blocks=[],
        family_blocks=[],
        personal_time_blocks=[],
        notes=""
    )
    return DailyRhythmProfileService.create(db, data)
