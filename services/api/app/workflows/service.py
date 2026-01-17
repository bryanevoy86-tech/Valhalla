from sqlalchemy.orm import Session
from .models import Workflow
from .schemas import WorkflowCreate


def create_workflow(db: Session, workflow: WorkflowCreate) -> Workflow:
    db_workflow = Workflow(
        task_name=workflow.task_name,
        status=workflow.status,  # type: ignore[arg-type]
        start_time=workflow.start_time,
        end_time=workflow.end_time,
        result=workflow.result,
    )
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    return db_workflow


def get_workflows(db: Session) -> list[Workflow]:
    return db.query(Workflow).all()
