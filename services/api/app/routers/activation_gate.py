"""
PACK CL17: Activation Gates Router
Prefix: /system/activation
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.activation_gate import (
    ActivationGateUpsert,
    ActivationGateLock,
    ActivationGateOut,
    ActivationGateList,
)
from app.services.activation_gate import upsert_gate, lock_gate, list_gates

router = APIRouter(prefix="/system/activation", tags=["System", "Activation"])


@router.post("/gates", response_model=ActivationGateOut, status_code=201)
def create_or_update_gate(payload: ActivationGateUpsert, db: Session = Depends(get_db)):
    return upsert_gate(db, payload)


@router.post("/gates/{gate_key}/lock", response_model=ActivationGateOut)
def set_gate_lock(gate_key: str, payload: ActivationGateLock, db: Session = Depends(get_db)):
    obj = lock_gate(db, gate_key, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Gate not found")
    return obj


@router.get("/gates", response_model=ActivationGateList)
def get_gates(limit: int = Query(500, ge=1, le=5000), db: Session = Depends(get_db)):
    items = list_gates(db, limit=limit)
    return ActivationGateList(total=len(items), items=[ActivationGateOut.model_validate(i) for i in items])
