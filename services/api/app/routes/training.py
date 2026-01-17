"""PACK 88: Training Engine - Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.training import TrainingModuleOut, TrainingModuleCreate, TrainingProgressOut, TrainingProgressCreate
from app.services.training_service import (
    create_training_module, list_training_modules, get_training_module, update_training_module, delete_training_module,
    create_progress, list_progress, get_progress, update_progress, delete_progress
)

router = APIRouter(prefix="/training", tags=["training"])


# Training module endpoints
@router.post("/module", response_model=TrainingModuleOut)
def post_training_module(module: TrainingModuleCreate, db: Session = Depends(get_db)):
    return create_training_module(db, module)


@router.get("/modules", response_model=list[TrainingModuleOut])
def get_modules_endpoint(db: Session = Depends(get_db)):
    return list_training_modules(db)


@router.get("/module/{module_id}", response_model=TrainingModuleOut)
def get_module_endpoint(module_id: int, db: Session = Depends(get_db)):
    return get_training_module(db, module_id)


@router.put("/module/{module_id}", response_model=TrainingModuleOut)
def put_training_module(module_id: int, module: TrainingModuleCreate, db: Session = Depends(get_db)):
    return update_training_module(db, module_id, module)


@router.delete("/module/{module_id}")
def delete_module_endpoint(module_id: int, db: Session = Depends(get_db)):
    return delete_training_module(db, module_id)


# Training progress endpoints
@router.post("/progress", response_model=TrainingProgressOut)
def post_progress(progress: TrainingProgressCreate, db: Session = Depends(get_db)):
    return create_progress(db, progress)


@router.get("/progress", response_model=list[TrainingProgressOut])
def get_progress_endpoint(user_id: int | None = None, db: Session = Depends(get_db)):
    return list_progress(db, user_id)


@router.get("/progress/{progress_id}", response_model=TrainingProgressOut)
def get_progress_by_id(progress_id: int, db: Session = Depends(get_db)):
    return get_progress(db, progress_id)


@router.put("/progress/{progress_id}", response_model=TrainingProgressOut)
def put_progress(progress_id: int, progress: TrainingProgressCreate, db: Session = Depends(get_db)):
    return update_progress(db, progress_id, progress)


@router.delete("/progress/{progress_id}")
def delete_progress_endpoint(progress_id: int, db: Session = Depends(get_db)):
    return delete_progress(db, progress_id)
