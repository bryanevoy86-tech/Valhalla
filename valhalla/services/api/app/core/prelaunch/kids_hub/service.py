"""Kids Hub Service Layer"""
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from . import models, schemas


def list_children(db: Session) -> List[models.PrelaunchKidsHubChildProfile]:
    """List all children."""
    return db.query(models.PrelaunchKidsHubChildProfile).order_by(models.PrelaunchKidsHubChildProfile.created_at).all()


def create_child(db: Session, data: schemas.ChildProfileCreate) -> models.PrelaunchKidsHubChildProfile:
    """Create a new child profile."""
    c = models.PrelaunchKidsHubChildProfile(**data.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def list_tasks_for_child(db: Session, child_id: UUID) -> List[models.ChildTask]:
    """List all tasks for a specific child."""
    return (
        db.query(models.ChildTask)
        .filter(models.ChildTask.child_id == child_id)
        .order_by(models.ChildTask.created_at)
        .all()
    )


def create_task_for_child(
    db: Session, child_id: UUID, data: schemas.ChildTaskCreate
) -> models.ChildTask:
    """Create a new task for a child."""
    t = models.ChildTask(child_id=child_id, **data.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def mark_task_done(db: Session, task: models.ChildTask) -> models.ChildTask:
    """Mark a task as done."""
    task.status = "DONE"
    db.commit()
    db.refresh(task)
    return task
