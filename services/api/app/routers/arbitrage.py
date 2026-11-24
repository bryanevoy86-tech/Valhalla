from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.services.prime_business_execution import _emergency_stop_active, require_owner_mandate_key
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


router = APIRouter(prefix="/arbitrage", tags=["arbitrage"], dependencies=[Depends(require_prime_control_key)])


def require_paper_write(db: Session = Depends(get_db), _: None = Depends(require_owner_mandate_key)):
    if _emergency_stop_active(db):
        raise HTTPException(503, "Paper FX paused by emergency stop")


paper_write = [Depends(require_paper_write)]


@router.post("/rules", response_model=FXRuleResponse, dependencies=paper_write)
def new_rule(payload: FXRuleCreate, db: Session = Depends(get_db)):
    return create_rule(db, payload)


@router.get("/rules", response_model=List[FXRuleResponse])
def rules(db: Session = Depends(get_db)):
    return list_rules(db)


@router.post("/orders", response_model=FXOrderResponse, dependencies=paper_write)
def new_order(payload: FXOrderCreate, db: Session = Depends(get_db)):
    return place_order(db, payload)


@router.get("/orders", response_model=List[FXOrderResponse])
def orders(status: Optional[str] = None, db: Session = Depends(get_db)):
    return list_orders(db, status)


@router.post("/orders/{order_id}/close", response_model=FXOrderResponse, dependencies=paper_write)
def close(order_id: int, body: FXCloseRequest, db: Session = Depends(get_db)):
    try:
        o = close_order(db, order_id, body.exit_px)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    if o is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return o


@router.post("/metrics/eval", response_model=FXMetricResponse, dependencies=paper_write)
def eval_metrics(db: Session = Depends(get_db)):
    return evaluate_and_record_metrics(db)


@router.post("/rules/bootstrap", dependencies=paper_write)
def bootstrap(db: Session = Depends(get_db)):
    bootstrap_safe_rules(db)
    return {"ok": True}
