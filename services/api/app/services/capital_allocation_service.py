"""PACK 62: Capital Allocation Service
Service layer for capital allocation operations.
"""

from sqlalchemy.orm import Session

from app.models.capital_allocation import CapitalAllocation


def save_allocation(
    db: Session,
    arbitrage_pct: float,
    vault_pct: float,
    shield_pct: float
) -> CapitalAllocation:
    """Save a new capital allocation."""
    allocation = CapitalAllocation(
        arbitrage_pct=arbitrage_pct,
        vault_pct=vault_pct,
        shield_pct=shield_pct,
    )
    db.add(allocation)
    db.commit()
    db.refresh(allocation)
    return allocation


def latest_allocation(db: Session) -> CapitalAllocation:
    """Get the latest capital allocation."""
    return db.query(CapitalAllocation).order_by(CapitalAllocation.id.desc()).first()
