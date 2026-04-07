"""
Module 76: Disposition Router
FastAPI endpoints for buyer matching and disposition.
"""
from fastapi import APIRouter
from app.buyers.store import BUYERS
from app.buyers.matcher import match_buyers


router = APIRouter(prefix="/buyers", tags=["Buyers"])


@router.post("/match")
def match(payload: dict):
    """
    Match lead to buyers by buy-box criteria.
    
    Args:
        payload: Lead data dict
            {
                "city": "Denver",
                "state": "CO",
                "arv": 350000,
                "asking_price": 250000
            }
    
    Returns:
        dict: Matching buyers list
    """
    try:
        buyers = BUYERS.list()
        matches = match_buyers(payload, buyers)
        return {"ok": True, "matches": matches}
    except Exception as e:
        return {"ok": False, "error": str(e)}
