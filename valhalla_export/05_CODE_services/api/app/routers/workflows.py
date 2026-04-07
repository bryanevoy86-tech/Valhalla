from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.workflows.schemas import WorkflowCreate, WorkflowResponse
from app.workflows.service import create_workflow, get_workflows


router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/", response_model=WorkflowResponse)
def create_workflow_route(workflow: WorkflowCreate, db: Session = Depends(get_db)):
    return create_workflow(db=db, workflow=workflow)


@router.get("/", response_model=List[WorkflowResponse])
def list_all_workflows(db: Session = Depends(get_db)):
    return get_workflows(db=db)
