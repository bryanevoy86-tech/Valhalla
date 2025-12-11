"""Family OS Router"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db

from . import schemas, service, models

router = APIRouter(prefix="/family", tags=["family_os"])


@router.get("/values", response_model=schemas.FamilyValuesRead)
def read_values(db: Session = Depends(get_db)):
    """Get family values, mission, and rules."""
    fv = service.get_family_values(db)
    return schemas.FamilyValuesRead.model_validate(fv)


@router.patch("/values", response_model=schemas.FamilyValuesRead)
def patch_values(
    payload: schemas.FamilyValuesUpdate,
    db: Session = Depends(get_db),
):
    """Update family values."""
    fv = service.update_family_values(db, payload)
    return schemas.FamilyValuesRead.model_validate(fv)


@router.get("/routines", response_model=List[schemas.FamilyRoutineRead])
def get_routines(db: Session = Depends(get_db)):
    """List all family routines."""
    routines = service.list_routines(db)
    return [schemas.FamilyRoutineRead.model_validate(r) for r in routines]


@router.post("/routines", response_model=schemas.FamilyRoutineRead)
def create_routine(
    payload: schemas.FamilyRoutineCreate,
    db: Session = Depends(get_db),
):
    """Create a new family routine."""
    r = service.create_routine(db, payload)
    return schemas.FamilyRoutineRead.model_validate(r)


@router.patch("/routines/{routine_id}", response_model=schemas.FamilyRoutineRead)
def update_routine(
    routine_id: UUID,
    payload: schemas.FamilyRoutineUpdate,
    db: Session = Depends(get_db),
):
    """Update a family routine."""
    r = db.query(models.FamilyRoutine).filter(models.FamilyRoutine.id == routine_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found")
    updated = service.update_routine(db, r, payload)
    return schemas.FamilyRoutineRead.model_validate(updated)


@router.get("/screentime", response_model=List[schemas.ScreenTimeRuleRead])
def get_screentime_rules(db: Session = Depends(get_db)):
    """List all screen time rules."""
    rules = service.list_screen_time_rules(db)
    return [schemas.ScreenTimeRuleRead.model_validate(r) for r in rules]


@router.post("/screentime", response_model=schemas.ScreenTimeRuleRead)
def create_screentime_rule(
    payload: schemas.ScreenTimeRuleCreate,
    db: Session = Depends(get_db),
):
    """Create a new screen time rule."""
    r = service.create_screen_time_rule(db, payload)
    return schemas.ScreenTimeRuleRead.model_validate(r)


@router.patch("/screentime/{rule_id}", response_model=schemas.ScreenTimeRuleRead)
def update_screentime_rule(
    rule_id: UUID,
    payload: schemas.ScreenTimeRuleUpdate,
    db: Session = Depends(get_db),
):
    """Update a screen time rule."""
    r = db.query(models.ScreenTimeRule).filter(models.ScreenTimeRule.id == rule_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Screen time rule not found")
    updated = service.update_screen_time_rule(db, r, payload)
    return schemas.ScreenTimeRuleRead.model_validate(updated)
