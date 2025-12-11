"""PACK 79: Curriculum Builder - Service"""

from sqlalchemy.orm import Session

from app.models.curriculum_builder import CurriculumUnit, AssignedUnit
from app.schemas.curriculum_builder import CurriculumUnitCreate, AssignedUnitCreate


# Curriculum unit operations
def create_curriculum_unit(db: Session, unit: CurriculumUnitCreate) -> CurriculumUnit:
    db_unit = CurriculumUnit(
        title=unit.title,
        grade_level=unit.grade_level,
        subject=unit.subject,
        content_payload=unit.content_payload
    )
    db.add(db_unit)
    db.commit()
    db.refresh(db_unit)
    return db_unit


def list_curriculum_units(db: Session) -> list[CurriculumUnit]:
    return db.query(CurriculumUnit).all()


def get_curriculum_unit(db: Session, unit_id: int) -> CurriculumUnit | None:
    return db.query(CurriculumUnit).filter(CurriculumUnit.id == unit_id).first()


def update_curriculum_unit(db: Session, unit_id: int, unit: CurriculumUnitCreate) -> CurriculumUnit | None:
    db_unit = get_curriculum_unit(db, unit_id)
    if not db_unit:
        return None
    db_unit.title = unit.title
    db_unit.grade_level = unit.grade_level
    db_unit.subject = unit.subject
    db_unit.content_payload = unit.content_payload
    db.commit()
    db.refresh(db_unit)
    return db_unit


def delete_curriculum_unit(db: Session, unit_id: int) -> bool:
    db_unit = get_curriculum_unit(db, unit_id)
    if not db_unit:
        return False
    db.delete(db_unit)
    db.commit()
    return True


# Assigned unit operations
def create_assigned_unit(db: Session, assigned: AssignedUnitCreate) -> AssignedUnit:
    db_assigned = AssignedUnit(
        classroom_id=assigned.classroom_id,
        unit_id=assigned.unit_id
    )
    db.add(db_assigned)
    db.commit()
    db.refresh(db_assigned)
    return db_assigned


def list_assigned_units_by_classroom(db: Session, classroom_id: int) -> list[AssignedUnit]:
    return db.query(AssignedUnit).filter(AssignedUnit.classroom_id == classroom_id).all()


def get_assigned_unit(db: Session, assigned_id: int) -> AssignedUnit | None:
    return db.query(AssignedUnit).filter(AssignedUnit.id == assigned_id).first()


def update_assigned_unit(db: Session, assigned_id: int, assigned: AssignedUnitCreate) -> AssignedUnit | None:
    db_assigned = get_assigned_unit(db, assigned_id)
    if not db_assigned:
        return None
    db_assigned.classroom_id = assigned.classroom_id
    db_assigned.unit_id = assigned.unit_id
    db.commit()
    db.refresh(db_assigned)
    return db_assigned


def delete_assigned_unit(db: Session, assigned_id: int) -> bool:
    db_assigned = get_assigned_unit(db, assigned_id)
    if not db_assigned:
        return False
    db.delete(db_assigned)
    db.commit()
    return True
