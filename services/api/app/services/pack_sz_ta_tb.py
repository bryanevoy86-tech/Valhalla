"""
Service classes for PACK SZ, TA, TB

Business logic for philosophy, relationships, and daily rhythm.
"""

from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from app.models.pack_sz import PhilosophyRecord, EmpirePrinciple, PhilosophySnapshot
from app.models.pack_ta import RelationshipProfile, TrustEventLog, RelationshipMapSnapshot
from app.models.pack_tb import DailyRhythmProfile, TempoRule, DailyTempoSnapshot
from app.schemas.pack_sz_ta_tb import (
    PhilosophyRecordCreate, PhilosophyRecordUpdate,
    EmpirePrincipleCreate, EmpirePrincipleUpdate,
    PhilosophySnapshotCreate, PhilosophySnapshotUpdate,
    RelationshipProfileCreate, RelationshipProfileUpdate,
    TrustEventLogCreate, TrustEventLogUpdate,
    RelationshipMapSnapshotCreate, RelationshipMapSnapshotUpdate,
    DailyRhythmProfileCreate, DailyRhythmProfileUpdate,
    TempoRuleCreate, TempoRuleUpdate,
    DailyTempoSnapshotCreate, DailyTempoSnapshotUpdate
)


def generate_id(prefix: str) -> str:
    """Generate unique ID with timestamp-based suffix."""
    timestamp = datetime.utcnow().strftime("%s")[-8:]
    return f"{prefix}-{timestamp}"


# =============================================================================
# PACK SZ: Core Philosophy & "Why I Built Valhalla" Archive
# =============================================================================

class PhilosophyRecordService:
    """Service for philosophy record management."""

    @staticmethod
    def create(db: Session, data: PhilosophyRecordCreate) -> PhilosophyRecord:
        """Create a philosophy record."""
        record = PhilosophyRecord(
            record_id=generate_id("phil"),
            title=data.title,
            date=data.date,
            pillars=data.pillars,
            mission_statement=data.mission_statement,
            values=data.values,
            rules_to_follow=data.rules_to_follow,
            rules_to_never_break=data.rules_to_never_break,
            long_term_intent=data.long_term_intent,
            notes=data.notes
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get(db: Session, record_id: int) -> Optional[PhilosophyRecord]:
        """Retrieve a philosophy record by ID."""
        return db.query(PhilosophyRecord).filter(PhilosophyRecord.id == record_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[PhilosophyRecord]:
        """List all philosophy records."""
        return db.query(PhilosophyRecord).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, record_id: int, data: PhilosophyRecordUpdate) -> Optional[PhilosophyRecord]:
        """Update a philosophy record."""
        record = PhilosophyRecordService.get(db, record_id)
        if not record:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(record, key, value)
        
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete(db: Session, record_id: int) -> bool:
        """Delete a philosophy record."""
        record = PhilosophyRecordService.get(db, record_id)
        if not record:
            return False
        
        db.delete(record)
        db.commit()
        return True


class EmpirePrincipleService:
    """Service for empire principle management."""

    @staticmethod
    def create(db: Session, data: EmpirePrincipleCreate) -> EmpirePrinciple:
        """Create an empire principle."""
        principle = EmpirePrinciple(
            principle_id=generate_id("prin"),
            record_id=data.record_id,
            category=data.category,
            description=data.description,
            enforcement_level=data.enforcement_level,
            notes=data.notes
        )
        db.add(principle)
        db.commit()
        db.refresh(principle)
        return principle

    @staticmethod
    def get(db: Session, principle_id: int) -> Optional[EmpirePrinciple]:
        """Retrieve an empire principle by ID."""
        return db.query(EmpirePrinciple).filter(EmpirePrinciple.id == principle_id).first()

    @staticmethod
    def list_by_record(db: Session, record_id: int) -> List[EmpirePrinciple]:
        """List principles for a philosophy record."""
        return db.query(EmpirePrinciple).filter(EmpirePrinciple.record_id == record_id).all()

    @staticmethod
    def list_by_category(db: Session, category: str, skip: int = 0, limit: int = 100) -> List[EmpirePrinciple]:
        """List principles by category."""
        return db.query(EmpirePrinciple).filter(EmpirePrinciple.category == category).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, principle_id: int, data: EmpirePrincipleUpdate) -> Optional[EmpirePrinciple]:
        """Update an empire principle."""
        principle = EmpirePrincipleService.get(db, principle_id)
        if not principle:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(principle, key, value)
        
        db.commit()
        db.refresh(principle)
        return principle

    @staticmethod
    def delete(db: Session, principle_id: int) -> bool:
        """Delete an empire principle."""
        principle = EmpirePrincipleService.get(db, principle_id)
        if not principle:
            return False
        
        db.delete(principle)
        db.commit()
        return True


class PhilosophySnapshotService:
    """Service for philosophy snapshot management."""

    @staticmethod
    def create(db: Session, data: PhilosophySnapshotCreate) -> PhilosophySnapshot:
        """Create a philosophy snapshot."""
        snapshot = PhilosophySnapshot(
            snapshot_id=generate_id("philsnap"),
            date=data.date,
            core_pillars=data.core_pillars,
            recent_updates=data.recent_updates,
            impact_on_system=data.impact_on_system,
            user_notes=data.user_notes
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    @staticmethod
    def get(db: Session, snapshot_id: int) -> Optional[PhilosophySnapshot]:
        """Retrieve a philosophy snapshot by ID."""
        return db.query(PhilosophySnapshot).filter(PhilosophySnapshot.id == snapshot_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[PhilosophySnapshot]:
        """List all philosophy snapshots."""
        return db.query(PhilosophySnapshot).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, snapshot_id: int, data: PhilosophySnapshotUpdate) -> Optional[PhilosophySnapshot]:
        """Update a philosophy snapshot."""
        snapshot = PhilosophySnapshotService.get(db, snapshot_id)
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
        """Delete a philosophy snapshot."""
        snapshot = PhilosophySnapshotService.get(db, snapshot_id)
        if not snapshot:
            return False
        
        db.delete(snapshot)
        db.commit()
        return True


# =============================================================================
# PACK TA: Trust, Loyalty & Relationship Mapping
# =============================================================================

class RelationshipProfileService:
    """Service for relationship profile management."""

    @staticmethod
    def create(db: Session, data: RelationshipProfileCreate) -> RelationshipProfile:
        """Create a relationship profile."""
        profile = RelationshipProfile(
            profile_id=generate_id("relprof"),
            name=data.name,
            role=data.role,
            relationship_type=data.relationship_type,
            user_defined_trust_level=data.user_defined_trust_level,
            boundaries=data.boundaries,
            notes=data.notes
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get(db: Session, profile_id: int) -> Optional[RelationshipProfile]:
        """Retrieve a relationship profile by ID."""
        return db.query(RelationshipProfile).filter(RelationshipProfile.id == profile_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[RelationshipProfile]:
        """List all relationship profiles."""
        return db.query(RelationshipProfile).offset(skip).limit(limit).all()

    @staticmethod
    def list_by_role(db: Session, role: str, skip: int = 0, limit: int = 100) -> List[RelationshipProfile]:
        """List profiles by role."""
        return db.query(RelationshipProfile).filter(RelationshipProfile.role == role).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, profile_id: int, data: RelationshipProfileUpdate) -> Optional[RelationshipProfile]:
        """Update a relationship profile."""
        profile = RelationshipProfileService.get(db, profile_id)
        if not profile:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)
        
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def delete(db: Session, profile_id: int) -> bool:
        """Delete a relationship profile."""
        profile = RelationshipProfileService.get(db, profile_id)
        if not profile:
            return False
        
        db.delete(profile)
        db.commit()
        return True


class TrustEventLogService:
    """Service for trust event log management."""

    @staticmethod
    def create(db: Session, data: TrustEventLogCreate) -> TrustEventLog:
        """Create a trust event log entry."""
        event = TrustEventLog(
            event_id=generate_id("trustevent"),
            profile_id=data.profile_id,
            date=data.date,
            event_description=data.event_description,
            trust_change=data.trust_change,
            notes=data.notes
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def get(db: Session, event_id: int) -> Optional[TrustEventLog]:
        """Retrieve a trust event log by ID."""
        return db.query(TrustEventLog).filter(TrustEventLog.id == event_id).first()

    @staticmethod
    def list_by_profile(db: Session, profile_id: int, skip: int = 0, limit: int = 100) -> List[TrustEventLog]:
        """List events for a relationship profile."""
        return db.query(TrustEventLog).filter(TrustEventLog.profile_id == profile_id).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, event_id: int, data: TrustEventLogUpdate) -> Optional[TrustEventLog]:
        """Update a trust event log entry."""
        event = TrustEventLogService.get(db, event_id)
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
        """Delete a trust event log entry."""
        event = TrustEventLogService.get(db, event_id)
        if not event:
            return False
        
        db.delete(event)
        db.commit()
        return True


class RelationshipMapSnapshotService:
    """Service for relationship map snapshot management."""

    @staticmethod
    def create(db: Session, data: RelationshipMapSnapshotCreate) -> RelationshipMapSnapshot:
        """Create a relationship map snapshot."""
        snapshot = RelationshipMapSnapshot(
            snapshot_id=generate_id("relsnap"),
            date=data.date,
            key_people=data.key_people,
            trust_levels=data.trust_levels,
            boundaries=data.boundaries,
            notes=data.notes
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    @staticmethod
    def get(db: Session, snapshot_id: int) -> Optional[RelationshipMapSnapshot]:
        """Retrieve a relationship map snapshot by ID."""
        return db.query(RelationshipMapSnapshot).filter(RelationshipMapSnapshot.id == snapshot_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[RelationshipMapSnapshot]:
        """List all relationship map snapshots."""
        return db.query(RelationshipMapSnapshot).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, snapshot_id: int, data: RelationshipMapSnapshotUpdate) -> Optional[RelationshipMapSnapshot]:
        """Update a relationship map snapshot."""
        snapshot = RelationshipMapSnapshotService.get(db, snapshot_id)
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
        """Delete a relationship map snapshot."""
        snapshot = RelationshipMapSnapshotService.get(db, snapshot_id)
        if not snapshot:
            return False
        
        db.delete(snapshot)
        db.commit()
        return True


# =============================================================================
# PACK TB: Daily Behavioral Rhythm & Tempo Engine
# =============================================================================

class DailyRhythmProfileService:
    """Service for daily rhythm profile management."""

    @staticmethod
    def create(db: Session, data: DailyRhythmProfileCreate) -> DailyRhythmProfile:
        """Create a daily rhythm profile."""
        profile = DailyRhythmProfile(
            profile_id=generate_id("rhythm"),
            wake_time=data.wake_time,
            sleep_time=data.sleep_time,
            peak_focus_blocks=[b.model_dump() for b in data.peak_focus_blocks],
            low_energy_blocks=[b.model_dump() for b in data.low_energy_blocks],
            family_blocks=[b.model_dump() for b in data.family_blocks],
            personal_time_blocks=[b.model_dump() for b in data.personal_time_blocks],
            notes=data.notes
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get(db: Session, profile_id: int) -> Optional[DailyRhythmProfile]:
        """Retrieve a daily rhythm profile by ID."""
        return db.query(DailyRhythmProfile).filter(DailyRhythmProfile.id == profile_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[DailyRhythmProfile]:
        """List all daily rhythm profiles."""
        return db.query(DailyRhythmProfile).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, profile_id: int, data: DailyRhythmProfileUpdate) -> Optional[DailyRhythmProfile]:
        """Update a daily rhythm profile."""
        profile = DailyRhythmProfileService.get(db, profile_id)
        if not profile:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key in ["peak_focus_blocks", "low_energy_blocks", "family_blocks", "personal_time_blocks"]:
                value = [b.model_dump() if hasattr(b, "model_dump") else b for b in value]
            setattr(profile, key, value)
        
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def delete(db: Session, profile_id: int) -> bool:
        """Delete a daily rhythm profile."""
        profile = DailyRhythmProfileService.get(db, profile_id)
        if not profile:
            return False
        
        db.delete(profile)
        db.commit()
        return True


class TempoRuleService:
    """Service for tempo rule management."""

    @staticmethod
    def create(db: Session, data: TempoRuleCreate) -> TempoRule:
        """Create a tempo rule."""
        rule = TempoRule(
            rule_id=generate_id("tempo"),
            profile_id=data.profile_id,
            time_block=data.time_block,
            action_intensity=data.action_intensity,
            communication_style=data.communication_style,
            notes=data.notes
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def get(db: Session, rule_id: int) -> Optional[TempoRule]:
        """Retrieve a tempo rule by ID."""
        return db.query(TempoRule).filter(TempoRule.id == rule_id).first()

    @staticmethod
    def list_by_profile(db: Session, profile_id: int) -> List[TempoRule]:
        """List tempo rules for a rhythm profile."""
        return db.query(TempoRule).filter(TempoRule.profile_id == profile_id).all()

    @staticmethod
    def update(db: Session, rule_id: int, data: TempoRuleUpdate) -> Optional[TempoRule]:
        """Update a tempo rule."""
        rule = TempoRuleService.get(db, rule_id)
        if not rule:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(rule, key, value)
        
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def delete(db: Session, rule_id: int) -> bool:
        """Delete a tempo rule."""
        rule = TempoRuleService.get(db, rule_id)
        if not rule:
            return False
        
        db.delete(rule)
        db.commit()
        return True


class DailyTempoSnapshotService:
    """Service for daily tempo snapshot management."""

    @staticmethod
    def create(db: Session, data: DailyTempoSnapshotCreate) -> DailyTempoSnapshot:
        """Create a daily tempo snapshot."""
        snapshot = DailyTempoSnapshot(
            snapshot_id=generate_id("daytemp"),
            date=data.date,
            rhythm_followed=data.rhythm_followed,
            adjustments_needed=data.adjustments_needed,
            user_notes=data.user_notes
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    @staticmethod
    def get(db: Session, snapshot_id: int) -> Optional[DailyTempoSnapshot]:
        """Retrieve a daily tempo snapshot by ID."""
        return db.query(DailyTempoSnapshot).filter(DailyTempoSnapshot.id == snapshot_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[DailyTempoSnapshot]:
        """List all daily tempo snapshots."""
        return db.query(DailyTempoSnapshot).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, snapshot_id: int, data: DailyTempoSnapshotUpdate) -> Optional[DailyTempoSnapshot]:
        """Update a daily tempo snapshot."""
        snapshot = DailyTempoSnapshotService.get(db, snapshot_id)
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
        """Delete a daily tempo snapshot."""
        snapshot = DailyTempoSnapshotService.get(db, snapshot_id)
        if not snapshot:
            return False
        
        db.delete(snapshot)
        db.commit()
        return True
