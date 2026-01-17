"""Family OS Service Layer"""
from sqlalchemy.orm import Session

from . import models, schemas


def get_family_values(db: Session) -> models.FamilyValues:
    """Get or create family values singleton."""
    fv = db.query(models.FamilyValues).first()
    if not fv:
        fv = models.FamilyValues(
            mission=None,
            core_values=[],
            rules=[],
        )
        db.add(fv)
        db.commit()
        db.refresh(fv)
    return fv


def update_family_values(
    db: Session, data: schemas.FamilyValuesUpdate
) -> models.FamilyValues:
    """Update family values."""
    fv = get_family_values(db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(fv, field, value)
    db.commit()
    db.refresh(fv)
    return fv


def list_routines(db: Session):
    """List all family routines."""
    return db.query(models.FamilyRoutine).order_by(models.FamilyRoutine.name).all()


def create_routine(db: Session, data: schemas.FamilyRoutineCreate):
    """Create a new family routine."""
    r = models.FamilyRoutine(**data.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def update_routine(db: Session, routine: models.FamilyRoutine, data: schemas.FamilyRoutineUpdate):
    """Update a family routine."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(routine, field, value)
    db.commit()
    db.refresh(routine)
    return routine


def list_screen_time_rules(db: Session):
    """List all screen time rules."""
    return db.query(models.ScreenTimeRule).order_by(models.ScreenTimeRule.age_group).all()


def create_screen_time_rule(db: Session, data: schemas.ScreenTimeRuleCreate):
    """Create a new screen time rule."""
    r = models.ScreenTimeRule(**data.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def update_screen_time_rule(
    db: Session,
    rule: models.ScreenTimeRule,
    data: schemas.ScreenTimeRuleUpdate,
):
    """Update a screen time rule."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule
