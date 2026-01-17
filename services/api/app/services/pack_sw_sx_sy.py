"""
Service classes for PACK SW, SX, SY

Business logic for life timeline, emotional stability, and strategic decisions.
"""

from datetime import datetime
from typing import Optional, List
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


def generate_id(prefix: str) -> str:
    """Generate unique ID with timestamp-based suffix."""
    timestamp = datetime.utcnow().strftime("%s")[-8:]
    return f"{prefix}-{timestamp}"


# =============================================================================
# PACK SW: Life Timeline & Major Milestones Engine
# =============================================================================

class LifeEventService:
    """Service for life event management."""

    @staticmethod
    def create(db: Session, data: LifeEventCreate) -> LifeEvent:
        """Create a new life event."""
        event = LifeEvent(
            event_id=generate_id("lifevnt"),
            date=data.date,
            title=data.title,
            category=data.category,
            description=data.description,
            impact_level=data.impact_level,
            notes=data.notes
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def get(db: Session, event_id: int) -> Optional[LifeEvent]:
        """Retrieve a life event by ID."""
        return db.query(LifeEvent).filter(LifeEvent.id == event_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[LifeEvent]:
        """List all life events."""
        return db.query(LifeEvent).offset(skip).limit(limit).all()

    @staticmethod
    def list_by_category(db: Session, category: str, skip: int = 0, limit: int = 100) -> List[LifeEvent]:
        """List life events by category."""
        return db.query(LifeEvent).filter(LifeEvent.category == category).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, event_id: int, data: LifeEventUpdate) -> Optional[LifeEvent]:
        """Update a life event."""
        event = LifeEventService.get(db, event_id)
        if not event:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(event, key, value)
        
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def delete(db: Session, event_id: int) -> bool:
        """Delete a life event."""
        event = LifeEventService.get(db, event_id)
        if not event:
            return False
        
        db.delete(event)
        db.commit()
        return True


class LifeMilestoneService:
    """Service for life milestone management."""

    @staticmethod
    def create(db: Session, data: LifeMilestoneCreate) -> LifeMilestone:
        """Create a new life milestone."""
        milestone = LifeMilestone(
            milestone_id=generate_id("lifemile"),
            event_id=data.event_id,
            milestone_type=data.milestone_type,
            description=data.description,
            notes=data.notes
        )
        db.add(milestone)
        db.commit()
        db.refresh(milestone)
        return milestone

    @staticmethod
    def get(db: Session, milestone_id: int) -> Optional[LifeMilestone]:
        """Retrieve a life milestone by ID."""
        return db.query(LifeMilestone).filter(LifeMilestone.id == milestone_id).first()

    @staticmethod
    def list_by_event(db: Session, event_id: int) -> List[LifeMilestone]:
        """List milestones for an event."""
        return db.query(LifeMilestone).filter(LifeMilestone.event_id == event_id).all()

    @staticmethod
    def update(db: Session, milestone_id: int, data: LifeMilestoneUpdate) -> Optional[LifeMilestone]:
        """Update a life milestone."""
        milestone = LifeMilestoneService.get(db, milestone_id)
        if not milestone:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(milestone, key, value)
        
        db.commit()
        db.refresh(milestone)
        return milestone

    @staticmethod
    def delete(db: Session, milestone_id: int) -> bool:
        """Delete a life milestone."""
        milestone = LifeMilestoneService.get(db, milestone_id)
        if not milestone:
            return False
        
        db.delete(milestone)
        db.commit()
        return True


class LifeTimelineSnapshotService:
    """Service for timeline snapshot management."""

    @staticmethod
    def create(db: Session, data: LifeTimelineSnapshotCreate) -> LifeTimelineSnapshot:
        """Create a timeline snapshot."""
        snapshot = LifeTimelineSnapshot(
            snapshot_id=generate_id("snapshot"),
            date_generated=data.date_generated,
            major_events=data.major_events,
            recent_changes=data.recent_changes,
            upcoming_milestones=data.upcoming_milestones,
            user_notes=data.user_notes
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    @staticmethod
    def get(db: Session, snapshot_id: int) -> Optional[LifeTimelineSnapshot]:
        """Retrieve a timeline snapshot by ID."""
        return db.query(LifeTimelineSnapshot).filter(LifeTimelineSnapshot.id == snapshot_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[LifeTimelineSnapshot]:
        """List all timeline snapshots."""
        return db.query(LifeTimelineSnapshot).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, snapshot_id: int, data: LifeTimelineSnapshotUpdate) -> Optional[LifeTimelineSnapshot]:
        """Update a timeline snapshot."""
        snapshot = LifeTimelineSnapshotService.get(db, snapshot_id)
        if not snapshot:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(snapshot, key, value)
        
        db.commit()
        db.refresh(snapshot)
        return snapshot

    @staticmethod
    def delete(db: Session, snapshot_id: int) -> bool:
        """Delete a timeline snapshot."""
        snapshot = LifeTimelineSnapshotService.get(db, snapshot_id)
        if not snapshot:
            return False
        
        db.delete(snapshot)
        db.commit()
        return True


# =============================================================================
# PACK SX: Emotional Neutrality & Stability Log
# =============================================================================

class EmotionalStateEntryService:
    """Service for emotional state entry management."""

    @staticmethod
    def create(db: Session, data: EmotionalStateEntryCreate) -> EmotionalStateEntry:
        """Create an emotional state entry."""
        entry = EmotionalStateEntry(
            entry_id=generate_id("emote"),
            date=data.date,
            self_reported_mood=data.self_reported_mood,
            energy_level=data.energy_level,
            cognitive_load=data.cognitive_load,
            context=data.context,
            notes=data.notes
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def get(db: Session, entry_id: int) -> Optional[EmotionalStateEntry]:
        """Retrieve an emotional state entry by ID."""
        return db.query(EmotionalStateEntry).filter(EmotionalStateEntry.id == entry_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[EmotionalStateEntry]:
        """List all emotional state entries."""
        return db.query(EmotionalStateEntry).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, entry_id: int, data: EmotionalStateEntryUpdate) -> Optional[EmotionalStateEntry]:
        """Update an emotional state entry."""
        entry = EmotionalStateEntryService.get(db, entry_id)
        if not entry:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(entry, key, value)
        
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def delete(db: Session, entry_id: int) -> bool:
        """Delete an emotional state entry."""
        entry = EmotionalStateEntryService.get(db, entry_id)
        if not entry:
            return False
        
        db.delete(entry)
        db.commit()
        return True


class StabilityLogService:
    """Service for stability log management."""

    @staticmethod
    def create(db: Session, data: StabilityLogCreate) -> StabilityLog:
        """Create a stability log entry."""
        log = StabilityLog(
            log_id=generate_id("stablog"),
            date=data.date,
            events_today=data.events_today,
            stress_factors=data.stress_factors,
            relief_actions=data.relief_actions,
            notes=data.notes
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get(db: Session, log_id: int) -> Optional[StabilityLog]:
        """Retrieve a stability log by ID."""
        return db.query(StabilityLog).filter(StabilityLog.id == log_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[StabilityLog]:
        """List all stability logs."""
        return db.query(StabilityLog).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, log_id: int, data: StabilityLogUpdate) -> Optional[StabilityLog]:
        """Update a stability log."""
        log = StabilityLogService.get(db, log_id)
        if not log:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(log, key, value)
        
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def delete(db: Session, log_id: int) -> bool:
        """Delete a stability log."""
        log = StabilityLogService.get(db, log_id)
        if not log:
            return False
        
        db.delete(log)
        db.commit()
        return True


class NeutralSummaryService:
    """Service for neutral summary management."""

    @staticmethod
    def create(db: Session, data: NeutralSummaryCreate) -> NeutralSummary:
        """Create a neutral summary."""
        summary = NeutralSummary(
            summary_id=generate_id("neusumm"),
            week_of=data.week_of,
            average_energy=data.average_energy,
            task_load=data.task_load,
            user_highlights=data.user_highlights,
            user_defined_interpretation=data.user_defined_interpretation
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)
        return summary

    @staticmethod
    def get(db: Session, summary_id: int) -> Optional[NeutralSummary]:
        """Retrieve a neutral summary by ID."""
        return db.query(NeutralSummary).filter(NeutralSummary.id == summary_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[NeutralSummary]:
        """List all neutral summaries."""
        return db.query(NeutralSummary).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_week(db: Session, week_of: str) -> Optional[NeutralSummary]:
        """Retrieve a neutral summary by week."""
        return db.query(NeutralSummary).filter(NeutralSummary.week_of == week_of).first()

    @staticmethod
    def update(db: Session, summary_id: int, data: NeutralSummaryUpdate) -> Optional[NeutralSummary]:
        """Update a neutral summary."""
        summary = NeutralSummaryService.get(db, summary_id)
        if not summary:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(summary, key, value)
        
        db.commit()
        db.refresh(summary)
        return summary

    @staticmethod
    def delete(db: Session, summary_id: int) -> bool:
        """Delete a neutral summary."""
        summary = NeutralSummaryService.get(db, summary_id)
        if not summary:
            return False
        
        db.delete(summary)
        db.commit()
        return True


# =============================================================================
# PACK SY: Strategic Decision History & Reason Archive
# =============================================================================

class StrategicDecisionService:
    """Service for strategic decision management."""

    @staticmethod
    def create(db: Session, data: StrategicDecisionCreate) -> StrategicDecision:
        """Create a strategic decision."""
        decision = StrategicDecision(
            decision_id=generate_id("strdec"),
            date=data.date,
            title=data.title,
            category=data.category,
            reasoning=data.reasoning,
            alternatives_considered=data.alternatives_considered,
            constraints=data.constraints,
            expected_outcome=data.expected_outcome,
            status=data.status,
            notes=data.notes
        )
        db.add(decision)
        db.commit()
        db.refresh(decision)
        return decision

    @staticmethod
    def get(db: Session, decision_id: int) -> Optional[StrategicDecision]:
        """Retrieve a strategic decision by ID."""
        return db.query(StrategicDecision).filter(StrategicDecision.id == decision_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[StrategicDecision]:
        """List all strategic decisions."""
        return db.query(StrategicDecision).offset(skip).limit(limit).all()

    @staticmethod
    def list_by_status(db: Session, status: str, skip: int = 0, limit: int = 100) -> List[StrategicDecision]:
        """List decisions by status."""
        return db.query(StrategicDecision).filter(StrategicDecision.status == status).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, decision_id: int, data: StrategicDecisionUpdate) -> Optional[StrategicDecision]:
        """Update a strategic decision."""
        decision = StrategicDecisionService.get(db, decision_id)
        if not decision:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(decision, key, value)
        
        db.commit()
        db.refresh(decision)
        return decision

    @staticmethod
    def delete(db: Session, decision_id: int) -> bool:
        """Delete a strategic decision."""
        decision = StrategicDecisionService.get(db, decision_id)
        if not decision:
            return False
        
        db.delete(decision)
        db.commit()
        return True


class DecisionRevisionService:
    """Service for decision revision management."""

    @staticmethod
    def create(db: Session, data: DecisionRevisionCreate) -> DecisionRevision:
        """Create a decision revision."""
        revision = DecisionRevision(
            revision_id=generate_id("decrev"),
            decision_id=data.decision_id,
            date=data.date,
            reason_for_revision=data.reason_for_revision,
            what_changed=data.what_changed,
            notes=data.notes
        )
        db.add(revision)
        db.commit()
        db.refresh(revision)
        return revision

    @staticmethod
    def get(db: Session, revision_id: int) -> Optional[DecisionRevision]:
        """Retrieve a decision revision by ID."""
        return db.query(DecisionRevision).filter(DecisionRevision.id == revision_id).first()

    @staticmethod
    def list_by_decision(db: Session, decision_id: int, skip: int = 0, limit: int = 100) -> List[DecisionRevision]:
        """List revisions for a decision."""
        return db.query(DecisionRevision).filter(DecisionRevision.decision_id == decision_id).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, revision_id: int, data: DecisionRevisionUpdate) -> Optional[DecisionRevision]:
        """Update a decision revision."""
        revision = DecisionRevisionService.get(db, revision_id)
        if not revision:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(revision, key, value)
        
        db.commit()
        db.refresh(revision)
        return revision

    @staticmethod
    def delete(db: Session, revision_id: int) -> bool:
        """Delete a decision revision."""
        revision = DecisionRevisionService.get(db, revision_id)
        if not revision:
            return False
        
        db.delete(revision)
        db.commit()
        return True


class DecisionChainSnapshotService:
    """Service for decision chain snapshot management."""

    @staticmethod
    def create(db: Session, data: DecisionChainSnapshotCreate) -> DecisionChainSnapshot:
        """Create a decision chain snapshot."""
        snapshot = DecisionChainSnapshot(
            snapshot_id=generate_id("decsnap"),
            date=data.date,
            major_decisions=data.major_decisions,
            revisions=data.revisions,
            reasons=data.reasons,
            system_impacts=data.system_impacts
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    @staticmethod
    def get(db: Session, snapshot_id: int) -> Optional[DecisionChainSnapshot]:
        """Retrieve a decision chain snapshot by ID."""
        return db.query(DecisionChainSnapshot).filter(DecisionChainSnapshot.id == snapshot_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[DecisionChainSnapshot]:
        """List all decision chain snapshots."""
        return db.query(DecisionChainSnapshot).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, snapshot_id: int, data: DecisionChainSnapshotUpdate) -> Optional[DecisionChainSnapshot]:
        """Update a decision chain snapshot."""
        snapshot = DecisionChainSnapshotService.get(db, snapshot_id)
        if not snapshot:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(snapshot, key, value)
        
        db.commit()
        db.refresh(snapshot)
        return snapshot

    @staticmethod
    def delete(db: Session, snapshot_id: int) -> bool:
        """Delete a decision chain snapshot."""
        snapshot = DecisionChainSnapshotService.get(db, snapshot_id)
        if not snapshot:
            return False
        
        db.delete(snapshot)
        db.commit()
        return True
