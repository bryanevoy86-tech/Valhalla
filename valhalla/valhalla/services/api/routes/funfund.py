from fastapi import APIRouter, Depends, HTTPException
from security.access import require_level

router = APIRouter()

# Simple in-memory number for now
CURRENT_BAL = {"balance": 0.0}


@router.get("/balance", dependencies=[Depends(require_level(1))])
def balance():
    return {"vault": "funfund", "balance": round(CURRENT_BAL["balance"], 2)}


@router.post("/deposit", dependencies=[Depends(require_level(25))])
def deposit(amount: float):
    if amount <= 0:
        raise HTTPException(400, "amount must be > 0")
    CURRENT_BAL["balance"] += amount
    return {"ok": True, "balance": round(CURRENT_BAL["balance"], 2)}


@router.post("/withdraw", dependencies=[Depends(require_level(25))])
def withdraw(amount: float):
    if amount <= 0:
        raise HTTPException(400, "amount must be > 0")
    if amount > CURRENT_BAL["balance"]:
        raise HTTPException(400, "insufficient funds")
    # Escalate rule example: > $10k needs Level 3 (we’ll enforce later)
    CURRENT_BAL["balance"] -= amount
    return {"ok": True, "balance": round(CURRENT_BAL["balance"], 2)}
