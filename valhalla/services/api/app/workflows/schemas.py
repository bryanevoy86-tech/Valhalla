from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class WorkflowStatusEnum(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class WorkflowBase(BaseModel):
    task_name: str
    status: WorkflowStatusEnum = WorkflowStatusEnum.pending
    start_time: datetime
    end_time: datetime | None = None
    result: str | None = None


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowResponse(WorkflowBase):
    id: int

    class Config:
        from_attributes = True
