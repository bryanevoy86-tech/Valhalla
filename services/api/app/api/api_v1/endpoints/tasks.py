from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.task import Task
from app.schemas.tasks import TaskCreate, TaskUpdate, TaskOut

router = APIRouter()


@router.post("/", response_model=TaskOut)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
):
    obj = Task(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[TaskOut])
def list_tasks(
    assignee: str | None = None,
    status: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Task)
    if assignee:
        query = query.filter(Task.assignee == assignee)
    if status:
        query = query.filter(Task.status == status)
    if category:
        query = query.filter(Task.category == category)
    return query.order_by(Task.priority.asc(), Task.created_at.desc()).all()


@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(Task).get(task_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    if payload.status == "done" and not obj.completed_at:
        obj.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return obj
