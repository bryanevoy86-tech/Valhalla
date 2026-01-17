"""
PACK Z: Global Holdings Engine Service
"""

from typing import List, Optional, Dict
from collections import defaultdict
from sqlalchemy.orm import Session

from app.models.holdings import Holding
from app.schemas.holdings import HoldingCreate, HoldingUpdate


def create_holding(db: Session, payload: HoldingCreate) -> Holding:
    obj = Holding(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_holding(
    db: Session,
    holding_id: int,
    payload: HoldingUpdate,
) -> Optional[Holding]:
    obj = db.query(Holding).filter(Holding.id == holding_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


def get_holding(db: Session, holding_id: int) -> Optional[Holding]:
    return db.query(Holding).filter(Holding.id == holding_id).first()


def list_holdings(
    db: Session,
    asset_type: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    only_active: bool = True,
) -> List[Holding]:
    q = db.query(Holding)
    if asset_type:
        q = q.filter(Holding.asset_type == asset_type)
    if jurisdiction:
        q = q.filter(Holding.jurisdiction == jurisdiction)
    if only_active:
        q = q.filter(Holding.is_active.is_(True))
    return q.order_by(Holding.created_at.desc()).all()


def summarize_holdings(db: Session) -> Dict:
    q = db.query(Holding).filter(Holding.is_active.is_(True)).all()

    total = 0.0
    by_type = defaultdict(float)
    by_jurisdiction = defaultdict(float)

    for h in q:
        if h.value_estimate is None:
            continue
        total += h.value_estimate
        by_type[h.asset_type] += h.value_estimate
        if h.jurisdiction:
            by_jurisdiction[h.jurisdiction] += h.value_estimate

    return {
        "total_value": total,
        "by_asset_type": dict(by_type),
        "by_jurisdiction": dict(by_jurisdiction),
    }
