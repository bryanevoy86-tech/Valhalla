"""PACK 84: Industry Engine - Revenue Simulator Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.industry_revenue import RevenueSimOut, RevenueSimCreate
from app.services.industry_revenue_service import (
    create_revenue_sim, list_revenue_sims, get_revenue_sim, update_revenue_sim, delete_revenue_sim
)

router = APIRouter(prefix="/industry/revenue", tags=["industry_revenue"])


@router.post("/", response_model=RevenueSimOut)
def post_revenue_sim(revenue_sim: RevenueSimCreate, db: Session = Depends(get_db)):
    return create_revenue_sim(db, revenue_sim)


@router.get("/", response_model=list[RevenueSimOut])
def get_revenue_sims_endpoint(industry_id: int | None = None, db: Session = Depends(get_db)):
    return list_revenue_sims(db, industry_id)


@router.get("/{sim_id}", response_model=RevenueSimOut)
def get_revenue_sim_endpoint(sim_id: int, db: Session = Depends(get_db)):
    return get_revenue_sim(db, sim_id)


@router.put("/{sim_id}", response_model=RevenueSimOut)
def put_revenue_sim(sim_id: int, revenue_sim: RevenueSimCreate, db: Session = Depends(get_db)):
    return update_revenue_sim(db, sim_id, revenue_sim)


@router.delete("/{sim_id}")
def delete_revenue_sim_endpoint(sim_id: int, db: Session = Depends(get_db)):
    return delete_revenue_sim(db, sim_id)
