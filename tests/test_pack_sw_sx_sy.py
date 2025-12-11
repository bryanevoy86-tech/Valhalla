"""
Test suite for PACK SW, SX, SY

Comprehensive tests for life timeline, emotional stability, and strategic decisions.
"""

import pytest
from datetime import date
from sqlalchemy.orm import Session

from app.models.pack_sw import LifeEvent, LifeMilestone, LifeTimelineSnapshot
from app.models.pack_sx import EmotionalStateEntry, StabilityLog, NeutralSummary
from app.models.pack_sy import StrategicDecision, DecisionRevision, DecisionChainSnapshot
from app.schemas.pack_sw_sx_sy import (
    LifeEventCreate, LifeEventUpdate,
    LifeMilestoneCreate, LifeMilestoneUpdate,
    LifeTimelineSnapshotCreate, LifeTimelineSnapshotUpdate,
    EmotionalStateEntryCreate, EmotionalStateEntryUpdate,
    StabilityLogCreate, StabilityLogUpdate,
    NeutralSummaryCreate, NeutralSummaryUpdate,
    StrategicDecisionCreate, StrategicDecisionUpdate,
    DecisionRevisionCreate, DecisionRevisionUpdate,
    DecisionChainSnapshotCreate, DecisionChainSnapshotUpdate
)
from app.services.pack_sw_sx_sy import (
    LifeEventService, LifeMilestoneService, LifeTimelineSnapshotService,
    EmotionalStateEntryService, StabilityLogService, NeutralSummaryService,
    StrategicDecisionService, DecisionRevisionService, DecisionChainSnapshotService
)


# =============================================================================
# PACK SW: Life Timeline & Major Milestones Engine Tests
# =============================================================================

class TestLifeEvent:
    """Test LifeEvent model and service."""

    def test_create_event(self, db: Session):
        """Test creating a life event."""
        data = LifeEventCreate(
            title="Started Business",
            date=date(2020, 1, 15),
            category="business",
            description="Launched first consulting practice",
            impact_level=5
        )
        event = LifeEventService.create(db, data)
        
        assert event.id is not None
        assert event.event_id.startswith("lifevnt-")
        assert event.title == "Started Business"
        assert event.impact_level == 5
        db.delete(event)
        db.commit()

    def test_list_events_by_category(self, db: Session):
        """Test listing events by category."""
        data1 = LifeEventCreate(
            title="Event 1",
            date=date(2020, 1, 1),
            category="business",
            description="Test",
            impact_level=3
        )
        data2 = LifeEventCreate(
            title="Event 2",
            date=date(2020, 2, 1),
            category="family",
            description="Test",
            impact_level=2
        )
        event1 = LifeEventService.create(db, data1)
        event2 = LifeEventService.create(db, data2)
        
        business_events = LifeEventService.list_by_category(db, "business")
        assert len(business_events) >= 1
        
        db.delete(event1)
        db.delete(event2)
        db.commit()

    def test_update_event(self, db: Session):
        """Test updating a life event."""
        data = LifeEventCreate(
            title="Original",
            date=date(2020, 1, 1),
            category="personal",
            description="Test",
            impact_level=1
        )
        created = LifeEventService.create(db, data)
        
        update_data = LifeEventUpdate(impact_level=5, title="Updated Title")
        updated = LifeEventService.update(db, created.id, update_data)
        
        assert updated.impact_level == 5
        assert updated.title == "Updated Title"
        db.delete(updated)
        db.commit()


class TestLifeMilestone:
    """Test LifeMilestone model and service."""

    def test_create_milestone(self, db: Session):
        """Test creating a life milestone."""
        event_data = LifeEventCreate(
            title="Test Event",
            date=date(2020, 1, 1),
            category="business",
            description="Test",
            impact_level=3
        )
        event = LifeEventService.create(db, event_data)
        
        milestone_data = LifeMilestoneCreate(
            event_id=event.id,
            milestone_type="start",
            description="Business launch milestone"
        )
        milestone = LifeMilestoneService.create(db, milestone_data)
        
        assert milestone.id is not None
        assert milestone.milestone_id.startswith("lifemile-")
        assert milestone.milestone_type == "start"
        
        db.delete(milestone)
        db.delete(event)
        db.commit()

    def test_list_milestones_by_event(self, db: Session):
        """Test listing milestones for an event."""
        event_data = LifeEventCreate(
            title="Test",
            date=date(2020, 1, 1),
            category="business",
            description="Test",
            impact_level=2
        )
        event = LifeEventService.create(db, event_data)
        
        mile_data1 = LifeMilestoneCreate(
            event_id=event.id,
            milestone_type="start",
            description="Start"
        )
        mile_data2 = LifeMilestoneCreate(
            event_id=event.id,
            milestone_type="finish",
            description="Finish"
        )
        mile1 = LifeMilestoneService.create(db, mile_data1)
        mile2 = LifeMilestoneService.create(db, mile_data2)
        
        milestones = LifeMilestoneService.list_by_event(db, event.id)
        assert len(milestones) >= 2
        
        db.delete(mile1)
        db.delete(mile2)
        db.delete(event)
        db.commit()


class TestLifeTimelineSnapshot:
    """Test LifeTimelineSnapshot model and service."""

    def test_create_snapshot(self, db: Session):
        """Test creating a timeline snapshot."""
        data = LifeTimelineSnapshotCreate(
            date_generated=date(2024, 12, 6),
            major_events=["lifevnt-001", "lifevnt-002"],
            recent_changes=["Changed focus", "New priority"],
            upcoming_milestones=["Launch product", "Hire team"]
        )
        snapshot = LifeTimelineSnapshotService.create(db, data)
        
        assert snapshot.id is not None
        assert snapshot.snapshot_id.startswith("snapshot-")
        assert len(snapshot.major_events) == 2
        db.delete(snapshot)
        db.commit()


# =============================================================================
# PACK SX: Emotional Neutrality & Stability Log Tests
# =============================================================================

class TestEmotionalStateEntry:
    """Test EmotionalStateEntry model and service."""

    def test_create_emotional_state(self, db: Session):
        """Test creating an emotional state entry."""
        data = EmotionalStateEntryCreate(
            date=date.today(),
            self_reported_mood="focused",
            energy_level=8,
            cognitive_load=6,
            context="Working on project X"
        )
        entry = EmotionalStateEntryService.create(db, data)
        
        assert entry.id is not None
        assert entry.entry_id.startswith("emote-")
        assert entry.energy_level == 8
        assert entry.self_reported_mood == "focused"
        db.delete(entry)
        db.commit()

    def test_list_emotional_states(self, db: Session):
        """Test listing emotional state entries."""
        data1 = EmotionalStateEntryCreate(
            date=date.today(),
            self_reported_mood="energetic",
            energy_level=9,
            cognitive_load=5,
            context="Context 1"
        )
        data2 = EmotionalStateEntryCreate(
            date=date.today(),
            self_reported_mood="tired",
            energy_level=4,
            cognitive_load=7,
            context="Context 2"
        )
        entry1 = EmotionalStateEntryService.create(db, data1)
        entry2 = EmotionalStateEntryService.create(db, data2)
        
        entries = EmotionalStateEntryService.list_all(db)
        assert len(entries) >= 2
        
        db.delete(entry1)
        db.delete(entry2)
        db.commit()


class TestStabilityLog:
    """Test StabilityLog model and service."""

    def test_create_stability_log(self, db: Session):
        """Test creating a stability log."""
        data = StabilityLogCreate(
            date=date.today(),
            events_today=["Meeting at 10am", "Completed report"],
            stress_factors=["Deadline approaching"],
            relief_actions=["Walked 30 min", "Meditated"]
        )
        log = StabilityLogService.create(db, data)
        
        assert log.id is not None
        assert log.log_id.startswith("stablog-")
        assert len(log.events_today) == 2
        assert len(log.relief_actions) == 2
        db.delete(log)
        db.commit()

    def test_update_stability_log(self, db: Session):
        """Test updating a stability log."""
        data = StabilityLogCreate(
            date=date.today(),
            events_today=["Event 1"],
            stress_factors=["Factor 1"],
            relief_actions=[]
        )
        created = StabilityLogService.create(db, data)
        
        update_data = StabilityLogUpdate(
            relief_actions=["Action 1", "Action 2"]
        )
        updated = StabilityLogService.update(db, created.id, update_data)
        
        assert len(updated.relief_actions) == 2
        db.delete(updated)
        db.commit()


class TestNeutralSummary:
    """Test NeutralSummary model and service."""

    def test_create_neutral_summary(self, db: Session):
        """Test creating a neutral summary."""
        data = NeutralSummaryCreate(
            week_of="2024-W49",
            average_energy=7.5,
            task_load=8.0,
            user_highlights=["Completed project", "Good week overall"],
            user_defined_interpretation="Productive week with good balance"
        )
        summary = NeutralSummaryService.create(db, data)
        
        assert summary.id is not None
        assert summary.summary_id.startswith("neusumm-")
        assert summary.average_energy == 7.5
        db.delete(summary)
        db.commit()

    def test_get_summary_by_week(self, db: Session):
        """Test retrieving summary by week."""
        data = NeutralSummaryCreate(
            week_of="2024-W50",
            average_energy=6.0,
            task_load=7.0
        )
        created = NeutralSummaryService.create(db, data)
        
        retrieved = NeutralSummaryService.get_by_week(db, "2024-W50")
        assert retrieved is not None
        assert retrieved.week_of == "2024-W50"
        db.delete(retrieved)
        db.commit()


# =============================================================================
# PACK SY: Strategic Decision History & Reason Archive Tests
# =============================================================================

class TestStrategicDecision:
    """Test StrategicDecision model and service."""

    def test_create_strategic_decision(self, db: Session):
        """Test creating a strategic decision."""
        data = StrategicDecisionCreate(
            date=date(2024, 1, 1),
            title="Pursue BRRRR Strategy",
            category="real_estate",
            reasoning="Better ROI than traditional rental properties",
            alternatives_considered=["Buy and hold", "Wholesaling"],
            constraints=["Limited capital", "Time availability"],
            expected_outcome="Build rental portfolio for cash flow"
        )
        decision = StrategicDecisionService.create(db, data)
        
        assert decision.id is not None
        assert decision.decision_id.startswith("strdec-")
        assert decision.status == "active"
        db.delete(decision)
        db.commit()

    def test_list_decisions_by_status(self, db: Session):
        """Test listing decisions by status."""
        data = StrategicDecisionCreate(
            date=date(2024, 1, 1),
            title="Decision",
            category="business",
            reasoning="Test reasoning",
            alternatives_considered=[],
            constraints=[],
            expected_outcome="Test outcome",
            status="completed"
        )
        decision = StrategicDecisionService.create(db, data)
        
        completed = StrategicDecisionService.list_by_status(db, "completed")
        assert len(completed) >= 1
        
        db.delete(decision)
        db.commit()

    def test_update_decision_status(self, db: Session):
        """Test updating decision status."""
        data = StrategicDecisionCreate(
            date=date(2024, 1, 1),
            title="Decision",
            category="finance",
            reasoning="Test",
            alternatives_considered=[],
            constraints=[],
            expected_outcome="Test",
            status="active"
        )
        created = StrategicDecisionService.create(db, data)
        
        update_data = StrategicDecisionUpdate(status="revised")
        updated = StrategicDecisionService.update(db, created.id, update_data)
        
        assert updated.status == "revised"
        db.delete(updated)
        db.commit()


class TestDecisionRevision:
    """Test DecisionRevision model and service."""

    def test_create_decision_revision(self, db: Session):
        """Test creating a decision revision."""
        decision_data = StrategicDecisionCreate(
            date=date(2024, 1, 1),
            title="Original Decision",
            category="business",
            reasoning="Original reasoning",
            alternatives_considered=[],
            constraints=[],
            expected_outcome="Original outcome"
        )
        decision = StrategicDecisionService.create(db, decision_data)
        
        revision_data = DecisionRevisionCreate(
            decision_id=decision.id,
            date=date(2024, 6, 1),
            reason_for_revision="Market conditions changed",
            what_changed="Shifted to focus on different market segment"
        )
        revision = DecisionRevisionService.create(db, revision_data)
        
        assert revision.id is not None
        assert revision.revision_id.startswith("decrev-")
        
        db.delete(revision)
        db.delete(decision)
        db.commit()

    def test_list_revisions_by_decision(self, db: Session):
        """Test listing revisions for a decision."""
        decision_data = StrategicDecisionCreate(
            date=date(2024, 1, 1),
            title="Decision",
            category="business",
            reasoning="Test",
            alternatives_considered=[],
            constraints=[],
            expected_outcome="Test"
        )
        decision = StrategicDecisionService.create(db, decision_data)
        
        rev_data1 = DecisionRevisionCreate(
            decision_id=decision.id,
            date=date(2024, 3, 1),
            reason_for_revision="Reason 1",
            what_changed="Change 1"
        )
        rev_data2 = DecisionRevisionCreate(
            decision_id=decision.id,
            date=date(2024, 6, 1),
            reason_for_revision="Reason 2",
            what_changed="Change 2"
        )
        rev1 = DecisionRevisionService.create(db, rev_data1)
        rev2 = DecisionRevisionService.create(db, rev_data2)
        
        revisions = DecisionRevisionService.list_by_decision(db, decision.id)
        assert len(revisions) >= 2
        
        db.delete(rev1)
        db.delete(rev2)
        db.delete(decision)
        db.commit()


class TestDecisionChainSnapshot:
    """Test DecisionChainSnapshot model and service."""

    def test_create_decision_snapshot(self, db: Session):
        """Test creating a decision chain snapshot."""
        data = DecisionChainSnapshotCreate(
            date=date(2024, 12, 6),
            major_decisions=["strdec-001", "strdec-002"],
            revisions=["Changed focus Q2", "Adjusted timeline Q3"],
            reasons=["Market feedback", "Resource availability"],
            system_impacts=["Portfolio shift", "Team restructuring"]
        )
        snapshot = DecisionChainSnapshotService.create(db, data)
        
        assert snapshot.id is not None
        assert snapshot.snapshot_id.startswith("decsnap-")
        assert len(snapshot.major_decisions) == 2
        db.delete(snapshot)
        db.commit()
