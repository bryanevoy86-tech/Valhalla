"""
FastAPI routers for PACK SW, SX, SY

REST API endpoints for life timeline, emotional stability, and strategic decisions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.schemas.pack_sw_sx_sy import (
    LifeEventCreate, LifeEventUpdate, LifeEventResponse,
    LifeMilestoneCreate, LifeMilestoneUpdate, LifeMilestoneResponse,
    LifeTimelineSnapshotCreate, LifeTimelineSnapshotUpdate, LifeTimelineSnapshotResponse,
    EmotionalStateEntryCreate, EmotionalStateEntryUpdate, EmotionalStateEntryResponse,
    StabilityLogCreate, StabilityLogUpdate, StabilityLogResponse,
    NeutralSummaryCreate, NeutralSummaryUpdate, NeutralSummaryResponse,
    StrategicDecisionCreate, StrategicDecisionUpdate, StrategicDecisionResponse,
    DecisionRevisionCreate, DecisionRevisionUpdate, DecisionRevisionResponse,
    DecisionChainSnapshotCreate, DecisionChainSnapshotUpdate, DecisionChainSnapshotResponse
)
from app.services.pack_sw_sx_sy import (
    LifeEventService, LifeMilestoneService, LifeTimelineSnapshotService,
    EmotionalStateEntryService, StabilityLogService, NeutralSummaryService,
    StrategicDecisionService, DecisionRevisionService, DecisionChainSnapshotService
)


# ============================================================================
# PACK SW: Life Timeline & Major Milestones Engine Router
# ============================================================================

router_sw = APIRouter(prefix="/api/v1/timeline", tags=["Life Timeline"])


# Life Events
@router_sw.post("/events", response_model=LifeEventResponse, status_code=status.HTTP_201_CREATED)
def create_event(data: LifeEventCreate, db: Session = Depends(get_db)):
    """Create a new life event."""
    return LifeEventService.create(db, data)


@router_sw.get("/events", response_model=List[LifeEventResponse])
def list_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all life events."""
    return LifeEventService.list_all(db, skip, limit)


@router_sw.get("/events/{event_id}", response_model=LifeEventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get a specific life event."""
    event = LifeEventService.get(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router_sw.get("/events/category/{category}", response_model=List[LifeEventResponse])
def list_events_by_category(category: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List events by category."""
    return LifeEventService.list_by_category(db, category, skip, limit)


@router_sw.put("/events/{event_id}", response_model=LifeEventResponse)
def update_event(event_id: int, data: LifeEventUpdate, db: Session = Depends(get_db)):
    """Update a life event."""
    event = LifeEventService.update(db, event_id, data)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router_sw.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    """Delete a life event."""
    if not LifeEventService.delete(db, event_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")


# Life Milestones
@router_sw.post("/milestones", response_model=LifeMilestoneResponse, status_code=status.HTTP_201_CREATED)
def create_milestone(data: LifeMilestoneCreate, db: Session = Depends(get_db)):
    """Create a new life milestone."""
    return LifeMilestoneService.create(db, data)


@router_sw.get("/milestones/{milestone_id}", response_model=LifeMilestoneResponse)
def get_milestone(milestone_id: int, db: Session = Depends(get_db)):
    """Get a specific milestone."""
    milestone = LifeMilestoneService.get(db, milestone_id)
    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")
    return milestone


@router_sw.get("/events/{event_id}/milestones", response_model=List[LifeMilestoneResponse])
def list_event_milestones(event_id: int, db: Session = Depends(get_db)):
    """List milestones for an event."""
    return LifeMilestoneService.list_by_event(db, event_id)


@router_sw.put("/milestones/{milestone_id}", response_model=LifeMilestoneResponse)
def update_milestone(milestone_id: int, data: LifeMilestoneUpdate, db: Session = Depends(get_db)):
    """Update a life milestone."""
    milestone = LifeMilestoneService.update(db, milestone_id, data)
    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")
    return milestone


@router_sw.delete("/milestones/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_milestone(milestone_id: int, db: Session = Depends(get_db)):
    """Delete a life milestone."""
    if not LifeMilestoneService.delete(db, milestone_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")


# Timeline Snapshots
@router_sw.post("/snapshots", response_model=LifeTimelineSnapshotResponse, status_code=status.HTTP_201_CREATED)
def create_snapshot(data: LifeTimelineSnapshotCreate, db: Session = Depends(get_db)):
    """Create a timeline snapshot."""
    return LifeTimelineSnapshotService.create(db, data)


@router_sw.get("/snapshots", response_model=List[LifeTimelineSnapshotResponse])
def list_snapshots(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all timeline snapshots."""
    return LifeTimelineSnapshotService.list_all(db, skip, limit)


@router_sw.get("/snapshots/{snapshot_id}", response_model=LifeTimelineSnapshotResponse)
def get_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """Get a specific snapshot."""
    snapshot = LifeTimelineSnapshotService.get(db, snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")
    return snapshot


@router_sw.put("/snapshots/{snapshot_id}", response_model=LifeTimelineSnapshotResponse)
def update_snapshot(snapshot_id: int, data: LifeTimelineSnapshotUpdate, db: Session = Depends(get_db)):
    """Update a timeline snapshot."""
    snapshot = LifeTimelineSnapshotService.update(db, snapshot_id, data)
    if not snapshot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")
    return snapshot


@router_sw.delete("/snapshots/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """Delete a timeline snapshot."""
    if not LifeTimelineSnapshotService.delete(db, snapshot_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")


# ============================================================================
# PACK SX: Emotional Neutrality & Stability Log Router
# ============================================================================

router_sx = APIRouter(prefix="/api/v1/emotional", tags=["Emotional Stability"])


# Emotional State Entries
@router_sx.post("/entries", response_model=EmotionalStateEntryResponse, status_code=status.HTTP_201_CREATED)
def create_state_entry(data: EmotionalStateEntryCreate, db: Session = Depends(get_db)):
    """Create an emotional state entry."""
    return EmotionalStateEntryService.create(db, data)


@router_sx.get("/entries", response_model=List[EmotionalStateEntryResponse])
def list_state_entries(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all emotional state entries."""
    return EmotionalStateEntryService.list_all(db, skip, limit)


@router_sx.get("/entries/{entry_id}", response_model=EmotionalStateEntryResponse)
def get_state_entry(entry_id: int, db: Session = Depends(get_db)):
    """Get a specific emotional state entry."""
    entry = EmotionalStateEntryService.get(db, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return entry


@router_sx.put("/entries/{entry_id}", response_model=EmotionalStateEntryResponse)
def update_state_entry(entry_id: int, data: EmotionalStateEntryUpdate, db: Session = Depends(get_db)):
    """Update an emotional state entry."""
    entry = EmotionalStateEntryService.update(db, entry_id, data)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return entry


@router_sx.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_state_entry(entry_id: int, db: Session = Depends(get_db)):
    """Delete an emotional state entry."""
    if not EmotionalStateEntryService.delete(db, entry_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")


# Stability Logs
@router_sx.post("/logs", response_model=StabilityLogResponse, status_code=status.HTTP_201_CREATED)
def create_stability_log(data: StabilityLogCreate, db: Session = Depends(get_db)):
    """Create a stability log entry."""
    return StabilityLogService.create(db, data)


@router_sx.get("/logs", response_model=List[StabilityLogResponse])
def list_stability_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all stability logs."""
    return StabilityLogService.list_all(db, skip, limit)


@router_sx.get("/logs/{log_id}", response_model=StabilityLogResponse)
def get_stability_log(log_id: int, db: Session = Depends(get_db)):
    """Get a specific stability log."""
    log = StabilityLogService.get(db, log_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    return log


@router_sx.put("/logs/{log_id}", response_model=StabilityLogResponse)
def update_stability_log(log_id: int, data: StabilityLogUpdate, db: Session = Depends(get_db)):
    """Update a stability log."""
    log = StabilityLogService.update(db, log_id, data)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    return log


@router_sx.delete("/logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stability_log(log_id: int, db: Session = Depends(get_db)):
    """Delete a stability log."""
    if not StabilityLogService.delete(db, log_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")


# Neutral Summaries
@router_sx.post("/summaries", response_model=NeutralSummaryResponse, status_code=status.HTTP_201_CREATED)
def create_neutral_summary(data: NeutralSummaryCreate, db: Session = Depends(get_db)):
    """Create a neutral summary."""
    return NeutralSummaryService.create(db, data)


@router_sx.get("/summaries", response_model=List[NeutralSummaryResponse])
def list_neutral_summaries(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all neutral summaries."""
    return NeutralSummaryService.list_all(db, skip, limit)


@router_sx.get("/summaries/{summary_id}", response_model=NeutralSummaryResponse)
def get_neutral_summary(summary_id: int, db: Session = Depends(get_db)):
    """Get a specific neutral summary."""
    summary = NeutralSummaryService.get(db, summary_id)
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found")
    return summary


@router_sx.get("/summaries/week/{week_of}", response_model=NeutralSummaryResponse)
def get_summary_by_week(week_of: str, db: Session = Depends(get_db)):
    """Get summary for a specific week."""
    summary = NeutralSummaryService.get_by_week(db, week_of)
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found")
    return summary


@router_sx.put("/summaries/{summary_id}", response_model=NeutralSummaryResponse)
def update_neutral_summary(summary_id: int, data: NeutralSummaryUpdate, db: Session = Depends(get_db)):
    """Update a neutral summary."""
    summary = NeutralSummaryService.update(db, summary_id, data)
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found")
    return summary


@router_sx.delete("/summaries/{summary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_neutral_summary(summary_id: int, db: Session = Depends(get_db)):
    """Delete a neutral summary."""
    if not NeutralSummaryService.delete(db, summary_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found")


# ============================================================================
# PACK SY: Strategic Decision History & Reason Archive Router
# ============================================================================

router_sy = APIRouter(prefix="/api/v1/decisions", tags=["Strategic Decisions"])


# Strategic Decisions
@router_sy.post("/", response_model=StrategicDecisionResponse, status_code=status.HTTP_201_CREATED)
def create_strategic_decision(data: StrategicDecisionCreate, db: Session = Depends(get_db)):
    """Create a new strategic decision."""
    return StrategicDecisionService.create(db, data)


@router_sy.get("/", response_model=List[StrategicDecisionResponse])
def list_strategic_decisions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all strategic decisions."""
    return StrategicDecisionService.list_all(db, skip, limit)


@router_sy.get("/{decision_id}", response_model=StrategicDecisionResponse)
def get_strategic_decision(decision_id: int, db: Session = Depends(get_db)):
    """Get a specific strategic decision."""
    decision = StrategicDecisionService.get(db, decision_id)
    if not decision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found")
    return decision


@router_sy.get("/status/{status}", response_model=List[StrategicDecisionResponse])
def list_decisions_by_status(status: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List decisions by status."""
    return StrategicDecisionService.list_by_status(db, status, skip, limit)


@router_sy.put("/{decision_id}", response_model=StrategicDecisionResponse)
def update_strategic_decision(decision_id: int, data: StrategicDecisionUpdate, db: Session = Depends(get_db)):
    """Update a strategic decision."""
    decision = StrategicDecisionService.update(db, decision_id, data)
    if not decision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found")
    return decision


@router_sy.delete("/{decision_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategic_decision(decision_id: int, db: Session = Depends(get_db)):
    """Delete a strategic decision."""
    if not StrategicDecisionService.delete(db, decision_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found")


# Decision Revisions
@router_sy.post("/revisions", response_model=DecisionRevisionResponse, status_code=status.HTTP_201_CREATED)
def create_decision_revision(data: DecisionRevisionCreate, db: Session = Depends(get_db)):
    """Create a decision revision."""
    return DecisionRevisionService.create(db, data)


@router_sy.get("/revisions/{revision_id}", response_model=DecisionRevisionResponse)
def get_decision_revision(revision_id: int, db: Session = Depends(get_db)):
    """Get a specific decision revision."""
    revision = DecisionRevisionService.get(db, revision_id)
    if not revision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found")
    return revision


@router_sy.get("/{decision_id}/revisions", response_model=List[DecisionRevisionResponse])
def list_decision_revisions(decision_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List revisions for a decision."""
    return DecisionRevisionService.list_by_decision(db, decision_id, skip, limit)


@router_sy.put("/revisions/{revision_id}", response_model=DecisionRevisionResponse)
def update_decision_revision(revision_id: int, data: DecisionRevisionUpdate, db: Session = Depends(get_db)):
    """Update a decision revision."""
    revision = DecisionRevisionService.update(db, revision_id, data)
    if not revision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found")
    return revision


@router_sy.delete("/revisions/{revision_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_decision_revision(revision_id: int, db: Session = Depends(get_db)):
    """Delete a decision revision."""
    if not DecisionRevisionService.delete(db, revision_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found")


# Decision Chain Snapshots
@router_sy.post("/snapshots", response_model=DecisionChainSnapshotResponse, status_code=status.HTTP_201_CREATED)
def create_decision_snapshot(data: DecisionChainSnapshotCreate, db: Session = Depends(get_db)):
    """Create a decision chain snapshot."""
    return DecisionChainSnapshotService.create(db, data)


@router_sy.get("/snapshots", response_model=List[DecisionChainSnapshotResponse])
def list_decision_snapshots(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all decision chain snapshots."""
    return DecisionChainSnapshotService.list_all(db, skip, limit)


@router_sy.get("/snapshots/{snapshot_id}", response_model=DecisionChainSnapshotResponse)
def get_decision_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """Get a specific decision chain snapshot."""
    snapshot = DecisionChainSnapshotService.get(db, snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")
    return snapshot


@router_sy.put("/snapshots/{snapshot_id}", response_model=DecisionChainSnapshotResponse)
def update_decision_snapshot(snapshot_id: int, data: DecisionChainSnapshotUpdate, db: Session = Depends(get_db)):
    """Update a decision chain snapshot."""
    snapshot = DecisionChainSnapshotService.update(db, snapshot_id, data)
    if not snapshot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")
    return snapshot


@router_sy.delete("/snapshots/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_decision_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """Delete a decision chain snapshot."""
    if not DecisionChainSnapshotService.delete(db, snapshot_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")
