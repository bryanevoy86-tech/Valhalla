"""
Module 68: Buyers Router
FastAPI endpoints for buyer directory management.
"""
from fastapi import APIRouter
from app.buyers.store import BUYERS, Buyer


router = APIRouter(prefix="/buyers", tags=["Buyers"])


@router.post("/upsert")
def upsert(payload: dict):
    """
    Insert or update buyer profile.
    
    Args:
        payload: Buyer data dict
            {
                "id": "buyer_123",
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "555-1234",
                "buy_box": {"city": "Denver", "state": "CO"}
            }
    
    Returns:
        dict: Success status and buyer data
    """
    try:
        b = Buyer(**payload)
        result = BUYERS.upsert(b)
        return {"ok": True, "buyer": result.__dict__}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("")
def list_buyers():
    """
    List all buyer profiles.
    
    Returns:
        dict: Success status and list of buyers
    """
    try:
        return {"ok": True, "buyers": BUYERS.list()}
    except Exception as e:
        return {"ok": False, "error": str(e)}
