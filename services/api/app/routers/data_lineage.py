"""
PACK AM: Data Lineage Router
Prefix: /lineage
"""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.data_lineage import DataLineageCreate, DataLineageOut
from app.services.data_lineage import record_lineage, list_lineage_for_entity

router = APIRouter(prefix="/lineage", tags=["Lineage"])


@router.post("/", response_model=DataLineageOut)
def record_lineage_endpoint(
    payload: DataLineageCreate,
    db: Session = Depends(get_db),
):
    """Record a lineage event for an entity."""
    return record_lineage(db, payload)


@router.get("/", response_model=List[DataLineageOut])
def list_lineage_endpoint(
    entity_type: str = Query(..., description="Entity type (deal, property, task, etc.)"),
    entity_id: str = Query(..., description="Entity ID"),
    limit: int = Query(50, ge=1, le=250),
    db: Session = Depends(get_db),
):
    """List lineage records for a specific entity."""
    return list_lineage_for_entity(db, entity_type, entity_id, limit)
