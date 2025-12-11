"""
FastAPI routers for PACK SZ, TA, TB

Philosophy, relationships, and daily rhythm endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.pack_sz_ta_tb import (
    PhilosophyRecordService, EmpirePrincipleService, PhilosophySnapshotService,
    RelationshipProfileService, TrustEventLogService, RelationshipMapSnapshotService,
    DailyRhythmProfileService, TempoRuleService, DailyTempoSnapshotService
)
from app.schemas.pack_sz_ta_tb import (
    PhilosophyRecordCreate, PhilosophyRecordUpdate, PhilosophyRecordResponse,
    EmpirePrincipleCreate, EmpirePrincipleUpdate, EmpirePrincipleResponse,
    PhilosophySnapshotCreate, PhilosophySnapshotUpdate, PhilosophySnapshotResponse,
    RelationshipProfileCreate, RelationshipProfileUpdate, RelationshipProfileResponse,
    TrustEventLogCreate, TrustEventLogUpdate, TrustEventLogResponse,
    RelationshipMapSnapshotCreate, RelationshipMapSnapshotUpdate, RelationshipMapSnapshotResponse,
    DailyRhythmProfileCreate, DailyRhythmProfileUpdate, DailyRhythmProfileResponse,
    TempoRuleCreate, TempoRuleUpdate, TempoRuleResponse,
    DailyTempoSnapshotCreate, DailyTempoSnapshotUpdate, DailyTempoSnapshotResponse
)

router_sz = APIRouter(prefix="/api/v1/philosophy", tags=["philosophy"])
router_ta = APIRouter(prefix="/api/v1/relationships", tags=["relationships"])
router_tb = APIRouter(prefix="/api/v1/rhythm", tags=["rhythm"])


# =============================================================================
# PACK SZ: Philosophy Records
# =============================================================================

@router_sz.post("/records", response_model=PhilosophyRecordResponse, status_code=201)
def create_philosophy_record(data: PhilosophyRecordCreate, db: Session = Depends(get_db)):
    """Create a new philosophy record."""
    return PhilosophyRecordService.create(db, data)


@router_sz.get("/records/{record_id}", response_model=PhilosophyRecordResponse)
def get_philosophy_record(record_id: int, db: Session = Depends(get_db)):
    """Retrieve a philosophy record."""
    record = PhilosophyRecordService.get(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Philosophy record not found")
    return record


@router_sz.get("/records", response_model=List[PhilosophyRecordResponse])
def list_philosophy_records(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all philosophy records."""
    return PhilosophyRecordService.list_all(db, skip, limit)


@router_sz.patch("/records/{record_id}", response_model=PhilosophyRecordResponse)
def update_philosophy_record(record_id: int, data: PhilosophyRecordUpdate, db: Session = Depends(get_db)):
    """Update a philosophy record."""
    record = PhilosophyRecordService.update(db, record_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Philosophy record not found")
    return record


@router_sz.delete("/records/{record_id}", status_code=204)
def delete_philosophy_record(record_id: int, db: Session = Depends(get_db)):
    """Delete a philosophy record."""
    if not PhilosophyRecordService.delete(db, record_id):
        raise HTTPException(status_code=404, detail="Philosophy record not found")


# =============================================================================
# PACK SZ: Empire Principles
# =============================================================================

@router_sz.post("/principles", response_model=EmpirePrincipleResponse, status_code=201)
def create_empire_principle(data: EmpirePrincipleCreate, db: Session = Depends(get_db)):
    """Create a new empire principle."""
    return EmpirePrincipleService.create(db, data)


@router_sz.get("/principles/{principle_id}", response_model=EmpirePrincipleResponse)
def get_empire_principle(principle_id: int, db: Session = Depends(get_db)):
    """Retrieve an empire principle."""
    principle = EmpirePrincipleService.get(db, principle_id)
    if not principle:
        raise HTTPException(status_code=404, detail="Empire principle not found")
    return principle


@router_sz.get("/records/{record_id}/principles", response_model=List[EmpirePrincipleResponse])
def list_principles_by_record(record_id: int, db: Session = Depends(get_db)):
    """List principles for a philosophy record."""
    return EmpirePrincipleService.list_by_record(db, record_id)


@router_sz.get("/principles/category/{category}", response_model=List[EmpirePrincipleResponse])
def list_principles_by_category(category: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List principles by category."""
    return EmpirePrincipleService.list_by_category(db, category, skip, limit)


@router_sz.patch("/principles/{principle_id}", response_model=EmpirePrincipleResponse)
def update_empire_principle(principle_id: int, data: EmpirePrincipleUpdate, db: Session = Depends(get_db)):
    """Update an empire principle."""
    principle = EmpirePrincipleService.update(db, principle_id, data)
    if not principle:
        raise HTTPException(status_code=404, detail="Empire principle not found")
    return principle


@router_sz.delete("/principles/{principle_id}", status_code=204)
def delete_empire_principle(principle_id: int, db: Session = Depends(get_db)):
    """Delete an empire principle."""
    if not EmpirePrincipleService.delete(db, principle_id):
        raise HTTPException(status_code=404, detail="Empire principle not found")


# =============================================================================
# PACK SZ: Philosophy Snapshots
# =============================================================================

@router_sz.post("/snapshots", response_model=PhilosophySnapshotResponse, status_code=201)
def create_philosophy_snapshot(data: PhilosophySnapshotCreate, db: Session = Depends(get_db)):
    """Create a new philosophy snapshot."""
    return PhilosophySnapshotService.create(db, data)


@router_sz.get("/snapshots/{snapshot_id}", response_model=PhilosophySnapshotResponse)
def get_philosophy_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """Retrieve a philosophy snapshot."""
    snapshot = PhilosophySnapshotService.get(db, snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Philosophy snapshot not found")
    return snapshot


@router_sz.get("/snapshots", response_model=List[PhilosophySnapshotResponse])
def list_philosophy_snapshots(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all philosophy snapshots."""
    return PhilosophySnapshotService.list_all(db, skip, limit)


@router_sz.patch("/snapshots/{snapshot_id}", response_model=PhilosophySnapshotResponse)
def update_philosophy_snapshot(snapshot_id: int, data: PhilosophySnapshotUpdate, db: Session = Depends(get_db)):
    """Update a philosophy snapshot."""
    snapshot = PhilosophySnapshotService.update(db, snapshot_id, data)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Philosophy snapshot not found")
    return snapshot


@router_sz.delete("/snapshots/{snapshot_id}", status_code=204)
def delete_philosophy_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """Delete a philosophy snapshot."""
    if not PhilosophySnapshotService.delete(db, snapshot_id):
        raise HTTPException(status_code=404, detail="Philosophy snapshot not found")


# =============================================================================
# PACK TA: Relationship Profiles
# =============================================================================

@router_ta.post("/profiles", response_model=RelationshipProfileResponse, status_code=201)
def create_relationship_profile(data: RelationshipProfileCreate, db: Session = Depends(get_db)):
    """Create a new relationship profile."""
    return RelationshipProfileService.create(db, data)


@router_ta.get("/profiles/{profile_id}", response_model=RelationshipProfileResponse)
def get_relationship_profile(profile_id: int, db: Session = Depends(get_db)):
    """Retrieve a relationship profile."""
    profile = RelationshipProfileService.get(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Relationship profile not found")
    return profile


@router_ta.get("/profiles", response_model=List[RelationshipProfileResponse])
def list_relationship_profiles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all relationship profiles."""
    return RelationshipProfileService.list_all(db, skip, limit)


@router_ta.get("/profiles/role/{role}", response_model=List[RelationshipProfileResponse])
def list_profiles_by_role(role: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List profiles by role."""
    return RelationshipProfileService.list_by_role(db, role, skip, limit)


@router_ta.patch("/profiles/{profile_id}", response_model=RelationshipProfileResponse)
def update_relationship_profile(profile_id: int, data: RelationshipProfileUpdate, db: Session = Depends(get_db)):
    """Update a relationship profile."""
    profile = RelationshipProfileService.update(db, profile_id, data)
    if not profile:
        raise HTTPException(status_code=404, detail="Relationship profile not found")
    return profile


@router_ta.delete("/profiles/{profile_id}", status_code=204)
def delete_relationship_profile(profile_id: int, db: Session = Depends(get_db)):
    """Delete a relationship profile."""
    if not RelationshipProfileService.delete(db, profile_id):
        raise HTTPException(status_code=404, detail="Relationship profile not found")


# =============================================================================
# PACK TA: Trust Event Logs
# =============================================================================

@router_ta.post("/events", response_model=TrustEventLogResponse, status_code=201)
def create_trust_event(data: TrustEventLogCreate, db: Session = Depends(get_db)):
    """Create a new trust event log entry."""
    return TrustEventLogService.create(db, data)


@router_ta.get("/events/{event_id}", response_model=TrustEventLogResponse)
def get_trust_event(event_id: int, db: Session = Depends(get_db)):
    """Retrieve a trust event log entry."""
    event = TrustEventLogService.get(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Trust event not found")
    return event


@router_ta.get("/profiles/{profile_id}/events", response_model=List[TrustEventLogResponse])
def list_events_by_profile(profile_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List trust events for a relationship profile."""
    return TrustEventLogService.list_by_profile(db, profile_id, skip, limit)


@router_ta.patch("/events/{event_id}", response_model=TrustEventLogResponse)
def update_trust_event(event_id: int, data: TrustEventLogUpdate, db: Session = Depends(get_db)):
    """Update a trust event log entry."""
    event = TrustEventLogService.update(db, event_id, data)
    if not event:
        raise HTTPException(status_code=404, detail="Trust event not found")
    return event


@router_ta.delete("/events/{event_id}", status_code=204)
def delete_trust_event(event_id: int, db: Session = Depends(get_db)):
    """Delete a trust event log entry."""
    if not TrustEventLogService.delete(db, event_id):
        raise HTTPException(status_code=404, detail="Trust event not found")


# =============================================================================
# PACK TA: Relationship Map Snapshots
# =============================================================================

@router_ta.post("/snapshots", response_model=RelationshipMapSnapshotResponse, status_code=201)
def create_relationship_snapshot(data: RelationshipMapSnapshotCreate, db: Session = Depends(get_db)):
    """Create a new relationship map snapshot."""
    return RelationshipMapSnapshotService.create(db, data)


@router_ta.get("/snapshots/{snapshot_id}", response_model=RelationshipMapSnapshotResponse)
def get_relationship_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """Retrieve a relationship map snapshot."""
    snapshot = RelationshipMapSnapshotService.get(db, snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Relationship map snapshot not found")
    return snapshot


@router_ta.get("/snapshots", response_model=List[RelationshipMapSnapshotResponse])
def list_relationship_snapshots(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all relationship map snapshots."""
    return RelationshipMapSnapshotService.list_all(db, skip, limit)


@router_ta.patch("/snapshots/{snapshot_id}", response_model=RelationshipMapSnapshotResponse)
def update_relationship_snapshot(snapshot_id: int, data: RelationshipMapSnapshotUpdate, db: Session = Depends(get_db)):
    """Update a relationship map snapshot."""
    snapshot = RelationshipMapSnapshotService.update(db, snapshot_id, data)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Relationship map snapshot not found")
    return snapshot


@router_ta.delete("/snapshots/{snapshot_id}", status_code=204)
def delete_relationship_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """Delete a relationship map snapshot."""
    if not RelationshipMapSnapshotService.delete(db, snapshot_id):
        raise HTTPException(status_code=404, detail="Relationship map snapshot not found")


# =============================================================================
# PACK TB: Daily Rhythm Profiles
# =============================================================================

@router_tb.post("/profiles", response_model=DailyRhythmProfileResponse, status_code=201)
def create_daily_rhythm_profile(data: DailyRhythmProfileCreate, db: Session = Depends(get_db)):
    """Create a new daily rhythm profile."""
    return DailyRhythmProfileService.create(db, data)


@router_tb.get("/profiles/{profile_id}", response_model=DailyRhythmProfileResponse)
def get_daily_rhythm_profile(profile_id: int, db: Session = Depends(get_db)):
    """Retrieve a daily rhythm profile."""
    profile = DailyRhythmProfileService.get(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Daily rhythm profile not found")
    return profile


@router_tb.get("/profiles", response_model=List[DailyRhythmProfileResponse])
def list_daily_rhythm_profiles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all daily rhythm profiles."""
    return DailyRhythmProfileService.list_all(db, skip, limit)


@router_tb.patch("/profiles/{profile_id}", response_model=DailyRhythmProfileResponse)
def update_daily_rhythm_profile(profile_id: int, data: DailyRhythmProfileUpdate, db: Session = Depends(get_db)):
    """Update a daily rhythm profile."""
    profile = DailyRhythmProfileService.update(db, profile_id, data)
    if not profile:
        raise HTTPException(status_code=404, detail="Daily rhythm profile not found")
    return profile


@router_tb.delete("/profiles/{profile_id}", status_code=204)
def delete_daily_rhythm_profile(profile_id: int, db: Session = Depends(get_db)):
    """Delete a daily rhythm profile."""
    if not DailyRhythmProfileService.delete(db, profile_id):
        raise HTTPException(status_code=404, detail="Daily rhythm profile not found")


# =============================================================================
# PACK TB: Tempo Rules
# =============================================================================

@router_tb.post("/rules", response_model=TempoRuleResponse, status_code=201)
def create_tempo_rule(data: TempoRuleCreate, db: Session = Depends(get_db)):
    """Create a new tempo rule."""
    return TempoRuleService.create(db, data)


@router_tb.get("/rules/{rule_id}", response_model=TempoRuleResponse)
def get_tempo_rule(rule_id: int, db: Session = Depends(get_db)):
    """Retrieve a tempo rule."""
    rule = TempoRuleService.get(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Tempo rule not found")
    return rule


@router_tb.get("/profiles/{profile_id}/rules", response_model=List[TempoRuleResponse])
def list_rules_by_profile(profile_id: int, db: Session = Depends(get_db)):
    """List tempo rules for a rhythm profile."""
    return TempoRuleService.list_by_profile(db, profile_id)


@router_tb.patch("/rules/{rule_id}", response_model=TempoRuleResponse)
def update_tempo_rule(rule_id: int, data: TempoRuleUpdate, db: Session = Depends(get_db)):
    """Update a tempo rule."""
    rule = TempoRuleService.update(db, rule_id, data)
    if not rule:
        raise HTTPException(status_code=404, detail="Tempo rule not found")
    return rule


@router_tb.delete("/rules/{rule_id}", status_code=204)
def delete_tempo_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete a tempo rule."""
    if not TempoRuleService.delete(db, rule_id):
        raise HTTPException(status_code=404, detail="Tempo rule not found")


# =============================================================================
# PACK TB: Daily Tempo Snapshots
# =============================================================================

@router_tb.post("/snapshots", response_model=DailyTempoSnapshotResponse, status_code=201)
def create_daily_tempo_snapshot(data: DailyTempoSnapshotCreate, db: Session = Depends(get_db)):
    """Create a new daily tempo snapshot."""
    return DailyTempoSnapshotService.create(db, data)


@router_tb.get("/snapshots/{snapshot_id}", response_model=DailyTempoSnapshotResponse)
def get_daily_tempo_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """Retrieve a daily tempo snapshot."""
    snapshot = DailyTempoSnapshotService.get(db, snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Daily tempo snapshot not found")
    return snapshot


@router_tb.get("/snapshots", response_model=List[DailyTempoSnapshotResponse])
def list_daily_tempo_snapshots(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all daily tempo snapshots."""
    return DailyTempoSnapshotService.list_all(db, skip, limit)


@router_tb.patch("/snapshots/{snapshot_id}", response_model=DailyTempoSnapshotResponse)
def update_daily_tempo_snapshot(snapshot_id: int, data: DailyTempoSnapshotUpdate, db: Session = Depends(get_db)):
    """Update a daily tempo snapshot."""
    snapshot = DailyTempoSnapshotService.update(db, snapshot_id, data)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Daily tempo snapshot not found")
    return snapshot


@router_tb.delete("/snapshots/{snapshot_id}", status_code=204)
def delete_daily_tempo_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """Delete a daily tempo snapshot."""
    if not DailyTempoSnapshotService.delete(db, snapshot_id):
        raise HTTPException(status_code=404, detail="Daily tempo snapshot not found")
