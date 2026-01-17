from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

from app.models.deal import Deal
from sqlalchemy import func
from sqlalchemy.orm import Session


def _now():
    return datetime.now(timezone.utc)


def _parse_range(r: str) -> datetime:
    n, unit = (int(r[:-1]), r[-1]) if r and r != "all" else (3650, "d")
    if unit == "d":
        return _now() - timedelta(days=n)
    if unit == "m":
        return _now() - timedelta(days=30 * n)
    return _now() - timedelta(days=3650)


def deals_by_status(db: Session, org_id: int, since: datetime) -> Dict[str, int]:
    q = (
        db.query(Deal.status, func.count(Deal.id))
        .filter(Deal.org_id == org_id)
        .filter(Deal.created_at >= since)
        .group_by(Deal.status)
    )
    return {k: v for (k, v) in q.all()}


def deals_timeseries_count(db: Session, org_id: int, since: datetime) -> List[Tuple[str, int]]:
    rows = (
        db.query(func.date_trunc("day", Deal.created_at), func.count(Deal.id))
        .filter(Deal.org_id == org_id, Deal.created_at >= since)
        .group_by(func.date_trunc("day", Deal.created_at))
        .order_by(func.date_trunc("day", Deal.created_at))
    )
    return [(d.isoformat(), c) for (d, c) in rows.all()]


def avg_deal_price(db: Session, org_id: int, since: datetime) -> float | None:
    row = (
        db.query(func.avg(Deal.price))
        .filter(Deal.org_id == org_id, Deal.created_at >= since)
        .first()
    )
    return float(row[0]) if row and row[0] is not None else None


REGISTRY = {
    "deals_by_status": deals_by_status,
    "deals_timeseries_count": deals_timeseries_count,
    "avg_deal_price": avg_deal_price,
}


def run_metric(db: Session, org_id: int, metric: str, range_str: str = "30d") -> Any:
    since = _parse_range(range_str)
    fn = REGISTRY.get(metric)
    if not fn:
        raise ValueError(f"Unknown metric: {metric}")
    return fn(db, org_id, since)
