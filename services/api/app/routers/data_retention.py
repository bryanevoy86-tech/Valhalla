"""
PACK UI: Data Retention Policy Registry Router
Prefix: /system/retention
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.data_retention import (
    DataRetentionSet,
    DataRetentionOut,
    DataRetentionList,
)
from app.services.data_retention import (
    set_retention_policy,
    list_retention_policies,
    get_retention_policy,
)

router = APIRouter(prefix="/system/retention", tags=["Data Retention"])


@router.post("/", response_model=DataRetentionOut)
def set_policy_endpoint(
    payload: DataRetentionSet,
    db: Session = Depends(get_db),
):
    return set_retention_policy(db, payload)


@router.get("/", response_model=DataRetentionList)
def list_policies_endpoint(
    db: Session = Depends(get_db),
):
    items = list_retention_policies(db)
    return DataRetentionList(total=len(items), items=items)


@router.get("/{category}", response_model=DataRetentionOut)
def get_policy_endpoint(
    category: str,
    db: Session = Depends(get_db),
):
    obj = get_retention_policy(db, category)
    if not obj:
        raise HTTPException(status_code=404, detail="Retention policy not found")
    return obj
