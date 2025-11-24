from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = "general"
    assignee: Optional[str] = "king"
    status: Optional[str] = "pending"
    priority: Optional[int] = 5
    due_at: Optional[datetime] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    category: Optional[str]
    assignee: Optional[str]
    status: Optional[str]
    priority: Optional[int]
    due_at: Optional[datetime]
    completed_at: Optional[datetime]


class TaskOut(TaskBase):
    id: int
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
