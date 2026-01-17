"""PACK 84: Industry Engine - Revenue Simulator Service"""

from sqlalchemy.orm import Session

from app.models.industry_revenue import IndustryRevenueSim
from app.schemas.industry_revenue import RevenueSimCreate


def create_revenue_sim(db: Session, revenue_sim: RevenueSimCreate) -> IndustryRevenueSim:
    db_sim = IndustryRevenueSim(
        industry_id=revenue_sim.industry_id,
        assumptions_payload=revenue_sim.assumptions_payload,
        low_estimate=revenue_sim.low_estimate,
        mid_estimate=revenue_sim.mid_estimate,
        high_estimate=revenue_sim.high_estimate
    )
    db.add(db_sim)
    db.commit()
    db.refresh(db_sim)
    return db_sim


def list_revenue_sims(db: Session, industry_id: int | None = None) -> list[IndustryRevenueSim]:
    q = db.query(IndustryRevenueSim)
    if industry_id:
        q = q.filter(IndustryRevenueSim.industry_id == industry_id)
    return q.order_by(IndustryRevenueSim.id.desc()).all()


def get_revenue_sim(db: Session, sim_id: int) -> IndustryRevenueSim | None:
    return db.query(IndustryRevenueSim).filter(IndustryRevenueSim.id == sim_id).first()


def update_revenue_sim(db: Session, sim_id: int, revenue_sim: RevenueSimCreate) -> IndustryRevenueSim | None:
    db_sim = get_revenue_sim(db, sim_id)
    if not db_sim:
        return None
    db_sim.industry_id = revenue_sim.industry_id
    db_sim.assumptions_payload = revenue_sim.assumptions_payload
    db_sim.low_estimate = revenue_sim.low_estimate
    db_sim.mid_estimate = revenue_sim.mid_estimate
    db_sim.high_estimate = revenue_sim.high_estimate
    db.commit()
    db.refresh(db_sim)
    return db_sim


def delete_revenue_sim(db: Session, sim_id: int) -> bool:
    db_sim = get_revenue_sim(db, sim_id)
    if not db_sim:
        return False
    db.delete(db_sim)
    db.commit()
    return True
