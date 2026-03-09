"""
PACK TM: Core Philosophy Archive Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.philosophy import PhilosophyRecord, EmpirePrinciple
from app.schemas.philosophy import (
    PhilosophyRecordCreate,
    EmpirePrincipleCreate,
    PhilosophySnapshot,
)


def create_philosophy_record(db: Session, payload: PhilosophyRecordCreate) -> PhilosophyRecord:
    obj = PhilosophyRecord(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_philosophy_records(db: Session) -> List[PhilosophyRecord]:
    return db.query(PhilosophyRecord).order_by(PhilosophyRecord.date.desc()).all()


def create_empire_principle(db: Session, payload: EmpirePrincipleCreate) -> EmpirePrinciple:
    obj = EmpirePrinciple(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_empire_principles(db: Session) -> List[EmpirePrinciple]:
    return db.query(EmpirePrinciple).order_by(EmpirePrinciple.category.asc()).all()


def get_philosophy_snapshot(db: Session) -> Optional[PhilosophySnapshot]:
    records = list_philosophy_records(db)
    if not records:
        return None
    principles = list_empire_principles(db)
    return PhilosophySnapshot(latest_record=records[0], principles=principles)
