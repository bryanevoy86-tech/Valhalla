from sqlalchemy import Column, Integer, String, Enum, DateTime
from datetime import datetime
import enum
from app.core.db import Base


class WorkflowStatusEnum(enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String, nullable=False)
    status = Column(Enum(WorkflowStatusEnum), default=WorkflowStatusEnum.pending)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    result = Column(String, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Workflow(task_name={self.task_name}, status={self.status})>"
