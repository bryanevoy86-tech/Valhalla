"""Kids Hub Router"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db

from . import schemas, service, models

router = APIRouter(prefix="/kids/hub", tags=["kids_hub"])


@router.get("/children", response_model=List[schemas.ChildProfileRead])
def get_children(db: Session = Depends(get_db)):
    """List all children."""
    children = service.list_children(db)
    return [schemas.ChildProfileRead.model_validate(c) for c in children]


@router.post("/children", response_model=schemas.ChildProfileRead)
def add_child(payload: schemas.ChildProfileCreate, db: Session = Depends(get_db)):
    """Create a new child profile."""
    c = service.create_child(db, payload)
    return schemas.ChildProfileRead.model_validate(c)


@router.get("/children/{child_id}/tasks", response_model=List[schemas.ChildTaskRead])
def child_tasks(child_id: UUID, db: Session = Depends(get_db)):
    """Get all tasks for a child."""
    tasks = service.list_tasks_for_child(db, child_id)
    return [schemas.ChildTaskRead.model_validate(t) for t in tasks]


@router.post("/children/{child_id}/tasks", response_model=schemas.ChildTaskRead)
def add_task(child_id: UUID, payload: schemas.ChildTaskCreate, db: Session = Depends(get_db)):
    """Create a new task for a child."""
    t = service.create_task_for_child(db, child_id, payload)
    return schemas.ChildTaskRead.model_validate(t)


@router.post("/tasks/{task_id}/done", response_model=schemas.ChildTaskRead)
def mark_done(task_id: UUID, db: Session = Depends(get_db)):
    """Mark a task as done."""
    t = db.query(models.ChildTask).filter(models.ChildTask.id == task_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    updated = service.mark_task_done(db, t)
    return schemas.ChildTaskRead.model_validate(updated)
