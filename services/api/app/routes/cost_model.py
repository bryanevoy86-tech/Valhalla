"""PACK 83: Industry Engine - Cost Model Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.cost_model import CostModelOut, CostModelCreate
from app.services.cost_model_service import (
    create_cost_model, list_cost_models, get_cost_model, update_cost_model, delete_cost_model
)

router = APIRouter(prefix="/industry/cost", tags=["cost_model"])


@router.post("/", response_model=CostModelOut)
def post_cost_model(cost_model: CostModelCreate, db: Session = Depends(get_db)):
    return create_cost_model(db, cost_model)


@router.get("/", response_model=list[CostModelOut])
def get_cost_models(product_line_id: int | None = None, db: Session = Depends(get_db)):
    return list_cost_models(db, product_line_id)


@router.get("/{cost_model_id}", response_model=CostModelOut)
def get_cost_model_endpoint(cost_model_id: int, db: Session = Depends(get_db)):
    return get_cost_model(db, cost_model_id)


@router.put("/{cost_model_id}", response_model=CostModelOut)
def put_cost_model(cost_model_id: int, cost_model: CostModelCreate, db: Session = Depends(get_db)):
    return update_cost_model(db, cost_model_id, cost_model)


@router.delete("/{cost_model_id}")
def delete_cost_model_endpoint(cost_model_id: int, db: Session = Depends(get_db)):
    return delete_cost_model(db, cost_model_id)
