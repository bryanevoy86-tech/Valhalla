from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.arbitrage.schemas import (
    FXRuleCreate,
    FXRuleResponse,
    FXOrderCreate,
    FXOrderResponse,
    FXCloseRequest,
    FXMetricResponse,
)
from app.arbitrage.service import (
    create_rule,
    list_rules,
    place_order,
    list_orders,
    close_order,
    evaluate_and_record_metrics,
    bootstrap_safe_rules,
)


router = APIRouter(prefix="/arbitrage", tags=["arbitrage"])


@router.post("/rules", response_model=FXRuleResponse)
def new_rule(payload: FXRuleCreate, db: Session = Depends(get_db)):
    return create_rule(db, payload)


@router.get("/rules", response_model=List[FXRuleResponse])
def rules(db: Session = Depends(get_db)):
    return list_rules(db)


@router.post("/orders", response_model=FXOrderResponse)
def new_order(payload: FXOrderCreate, db: Session = Depends(get_db)):
    return place_order(db, payload)


@router.get("/orders", response_model=List[FXOrderResponse])
def orders(status: Optional[str] = None, db: Session = Depends(get_db)):
    return list_orders(db, status)


@router.post("/orders/{order_id}/close", response_model=FXOrderResponse)
def close(order_id: int, body: FXCloseRequest, db: Session = Depends(get_db)):
    o = close_order(db, order_id, body.exit_px)
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    return o


@router.post("/metrics/eval", response_model=FXMetricResponse)
def eval_metrics(db: Session = Depends(get_db)):
    return evaluate_and_record_metrics(db)


@router.post("/rules/bootstrap")
def bootstrap(db: Session = Depends(get_db)):
    bootstrap_safe_rules(db)
    return {"ok": True}
