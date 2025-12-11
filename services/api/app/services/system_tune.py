"""
PACK TF: System Tune List Engine Service Layer
"""

from sqlalchemy.orm import Session
from app.models.system_tune import TuneArea, TuneItem
from app.schemas.system_tune import TuneAreaCreate, TuneItemCreate


def create_tune_area(db: Session, area: TuneAreaCreate) -> TuneArea:
    """Create a new tune area."""
    db_area = TuneArea(
        name=area.name,
        description=area.description,
    )
    db.add(db_area)
    db.commit()
    db.refresh(db_area)
    return db_area


def list_tune_areas(db: Session, skip: int = 0, limit: int = 100) -> list[TuneArea]:
    """List all tune areas."""
    return db.query(TuneArea).offset(skip).limit(limit).all()


def get_tune_area(db: Session, area_id: int) -> TuneArea | None:
    """Get a specific tune area by ID."""
    return db.query(TuneArea).filter(TuneArea.id == area_id).first()


def create_tune_item(db: Session, item: TuneItemCreate, area_id: int) -> TuneItem:
    """Create a new tune item in an area."""
    from datetime import datetime

    db_item = TuneItem(
        area_id=area_id,
        title=item.title,
        description=item.description,
        priority=item.priority,
        status=item.status or "pending",
        created_at=datetime.utcnow(),
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def list_tune_items(db: Session, skip: int = 0, limit: int = 100) -> list[TuneItem]:
    """List all tune items."""
    return db.query(TuneItem).offset(skip).limit(limit).all()


def get_tune_item(db: Session, item_id: int) -> TuneItem | None:
    """Get a specific tune item by ID."""
    return db.query(TuneItem).filter(TuneItem.id == item_id).first()


def update_tune_item_status(db: Session, item_id: int, status: str) -> TuneItem | None:
    """Update the status of a tune item."""
    from datetime import datetime

    db_item = db.query(TuneItem).filter(TuneItem.id == item_id).first()
    if db_item:
        db_item.status = status
        if status == "done":
            db_item.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(db_item)
    return db_item
