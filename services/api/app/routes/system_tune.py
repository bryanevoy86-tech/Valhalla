"""
PACK TF: System Tune List Engine Router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.system_tune import TuneAreaCreate, TuneAreaOut, TuneItemCreate, TuneItemOut
from app.services.system_tune import (
    create_tune_area,
    list_tune_areas,
    get_tune_area,
    create_tune_item,
    list_tune_items,
    get_tune_item,
    update_tune_item_status,
)

router = APIRouter(prefix="/system/tune", tags=["System Tune List"])


@router.post("/areas", response_model=TuneAreaOut)
def post_tune_area(area: TuneAreaCreate, db: Session = Depends(get_db)):
    """Create a new tune area."""
    return create_tune_area(db, area)


@router.get("/areas", response_model=list[TuneAreaOut])
def get_tune_areas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all tune areas."""
    return list_tune_areas(db, skip, limit)


@router.get("/areas/{area_id}", response_model=TuneAreaOut)
def get_one_area(area_id: int, db: Session = Depends(get_db)):
    """Get a specific tune area with its items."""
    db_area = get_tune_area(db, area_id)
    if not db_area:
        raise HTTPException(status_code=404, detail="Tune area not found")
    return db_area


@router.post("/areas/{area_id}/items", response_model=TuneItemOut)
def post_tune_item(
    area_id: int, item: TuneItemCreate, db: Session = Depends(get_db)
):
    """Create a new tune item in an area."""
    # Verify area exists
    if not get_tune_area(db, area_id):
        raise HTTPException(status_code=404, detail="Tune area not found")
    return create_tune_item(db, item, area_id)


@router.get("/items", response_model=list[TuneItemOut])
def get_tune_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all tune items."""
    return list_tune_items(db, skip, limit)


@router.get("/items/{item_id}", response_model=TuneItemOut)
def get_one_item(item_id: int, db: Session = Depends(get_db)):
    """Get a specific tune item."""
    db_item = get_tune_item(db, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Tune item not found")
    return db_item


@router.post("/items/{item_id}/status/{status}", response_model=TuneItemOut)
def update_item_status(item_id: int, status: str, db: Session = Depends(get_db)):
    """Update the status of a tune item (pending, in_progress, done, skipped)."""
    db_item = update_tune_item_status(db, item_id, status)
    if not db_item:
        raise HTTPException(status_code=404, detail="Tune item not found")
    return db_item
