"""
PACK AM: Data Lineage Engine Service
"""

from typing import List
from sqlalchemy.orm import Session

from app.models.data_lineage import DataLineage
from app.schemas.data_lineage import DataLineageCreate


def record_lineage(db: Session, payload: DataLineageCreate) -> DataLineage:
    obj = DataLineage(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_lineage_for_entity(
    db: Session,
    entity_type: str,
    entity_id: str,
    limit: int = 100,
) -> List[DataLineage]:
    return (
        db.query(DataLineage)
        .filter(DataLineage.entity_type == entity_type)
        .filter(DataLineage.entity_id == entity_id)
        .order_by(DataLineage.created_at.desc())
        .limit(limit)
        .all()
    )
