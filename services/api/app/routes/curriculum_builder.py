"""PACK 79: Curriculum Builder - Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.curriculum_builder import CurriculumUnitOut, CurriculumUnitCreate, AssignedUnitOut, AssignedUnitCreate
from app.services.curriculum_builder_service import (
    create_curriculum_unit, list_curriculum_units, get_curriculum_unit, update_curriculum_unit, delete_curriculum_unit,
    create_assigned_unit, list_assigned_units_by_classroom, get_assigned_unit, update_assigned_unit, delete_assigned_unit
)

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


# Curriculum unit endpoints
@router.post("/unit", response_model=CurriculumUnitOut)
def post_curriculum_unit(unit: CurriculumUnitCreate, db: Session = Depends(get_db)):
    return create_curriculum_unit(db, unit)


@router.get("/units", response_model=list[CurriculumUnitOut])
def get_curriculum_units(db: Session = Depends(get_db)):
    return list_curriculum_units(db)


@router.get("/unit/{unit_id}", response_model=CurriculumUnitOut)
def get_curriculum_unit_endpoint(unit_id: int, db: Session = Depends(get_db)):
    return get_curriculum_unit(db, unit_id)


@router.put("/unit/{unit_id}", response_model=CurriculumUnitOut)
def put_curriculum_unit(unit_id: int, unit: CurriculumUnitCreate, db: Session = Depends(get_db)):
    return update_curriculum_unit(db, unit_id, unit)


@router.delete("/unit/{unit_id}")
def delete_curriculum_unit_endpoint(unit_id: int, db: Session = Depends(get_db)):
    return delete_curriculum_unit(db, unit_id)


# Assigned unit endpoints
@router.post("/assigned", response_model=AssignedUnitOut)
def post_assigned_unit(assigned: AssignedUnitCreate, db: Session = Depends(get_db)):
    return create_assigned_unit(db, assigned)


@router.get("/assigned/{classroom_id}", response_model=list[AssignedUnitOut])
def get_assigned_units(classroom_id: int, db: Session = Depends(get_db)):
    return list_assigned_units_by_classroom(db, classroom_id)


@router.get("/assigned-item/{assigned_id}", response_model=AssignedUnitOut)
def get_assigned_unit_endpoint(assigned_id: int, db: Session = Depends(get_db)):
    return get_assigned_unit(db, assigned_id)


@router.put("/assigned/{assigned_id}", response_model=AssignedUnitOut)
def put_assigned_unit(assigned_id: int, assigned: AssignedUnitCreate, db: Session = Depends(get_db)):
    return update_assigned_unit(db, assigned_id, assigned)


@router.delete("/assigned/{assigned_id}")
def delete_assigned_unit_endpoint(assigned_id: int, db: Session = Depends(get_db)):
    return delete_assigned_unit(db, assigned_id)
