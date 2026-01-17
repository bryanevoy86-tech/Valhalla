from typing import Any

from sqlalchemy.orm import Session

from ..models.lead import Lead


def deals_pending_count(db: Session, org_id: int | None) -> int:
    # TODO: replace with your real query
    # return count of pending deals in this org
    return (
        db.query(Lead).filter(Lead.org_id == org_id, Lead.status == "pending").count()
        if org_id
        else 0
    )


PROVIDERS = {
    "deals_pending_count": deals_pending_count,
}


def get_metric(db: Session, org_id: int | None, name: str) -> Any:
    fn = PROVIDERS.get(name)
    if not fn:
        raise ValueError(f"Unknown metric: {name}")
    return fn(db, org_id)
