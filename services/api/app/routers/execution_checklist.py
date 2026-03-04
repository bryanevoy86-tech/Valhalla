"""
PACK CL15: Execution Checklist Router
Prefix: /system/execution
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.execution_checklist import (
    ExecutionChecklistItemCreate,
    ExecutionChecklistItemOut,
    ExecutionChecklistList,
)
from app.services.execution_checklist import upsert_item, list_items

router = APIRouter(prefix="/system/execution", tags=["System", "Readiness"])


@router.post("/checklist", response_model=ExecutionChecklistItemOut, status_code=201)
def create_or_update_checklist_item(payload: ExecutionChecklistItemCreate, db: Session = Depends(get_db)):
    return upsert_item(db, payload)


@router.get("/checklist", response_model=ExecutionChecklistList)
def get_checklist(limit: int = Query(500, ge=1, le=5000), db: Session = Depends(get_db)):
    items = list_items(db, limit=limit)
    return ExecutionChecklistList(total=len(items), items=[ExecutionChecklistItemOut.model_validate(i) for i in items])
