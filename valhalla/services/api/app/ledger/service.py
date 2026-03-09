"""Revenue ledger service - record all revenue events."""
import uuid
import json
from sqlalchemy.orm import Session
from app.ledger.models import RevenueEntry


def record_revenue(
    db: Session,
    engine: str,
    amount: int,
    source: str,
    meta: dict = None
) -> RevenueEntry:
    """
    Record a revenue event.
    
    Args:
        db: Database session
        engine: Which engine generated this revenue (e.g., "realestate", "contracts")
        amount: Amount in cents
        source: Source identifier (e.g., "deal_123", "contract_456")
        meta: Optional metadata dict
    """
    entry = RevenueEntry(
        id=f"rev_{uuid.uuid4().hex[:12]}",
        engine=engine,
        amount=amount,
        source=source,
        meta=json.dumps(meta or {})
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_revenue_by_engine(db: Session, engine: str, limit: int = 100):
    """Get recent revenue entries for a specific engine."""
    return db.query(RevenueEntry)\
        .filter(RevenueEntry.engine == engine)\
        .order_by(RevenueEntry.created_at.desc())\
        .limit(limit)\
        .all()


def get_total_revenue(db: Session, engine: str = None) -> int:
    """Get total revenue, optionally filtered by engine."""
    query = db.query(RevenueEntry)
    if engine:
        query = query.filter(RevenueEntry.engine == engine)
    
    result = query.with_entities(db.func.sum(RevenueEntry.amount)).scalar()
    return result or 0


def get_revenue_summary(db: Session) -> dict:
    """Get revenue summary by engine."""
    from sqlalchemy import func
    
    summary = db.query(
        RevenueEntry.engine,
        func.count(RevenueEntry.id).label("count"),
        func.sum(RevenueEntry.amount).label("total")
    ).group_by(RevenueEntry.engine).all()
    
    return {
        row[0]: {
            "count": row[1],
            "total": row[2] or 0
        }
        for row in summary
    }
