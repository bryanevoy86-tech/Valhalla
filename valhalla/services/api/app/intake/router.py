"""Deal intake router - REST endpoint for deal ingestion."""
from fastapi import APIRouter, HTTPException
from app.intake.service import create_deal
from app.core.runtime_flags import is_live

intake_router = APIRouter(prefix="/intake", tags=["intake"])


@intake_router.post("/deal")
def intake_deal(source: str, arv: float, purchase_price: float, payload: dict = None):
    """
    Intake a deal from external source.
    
    Args:
        source: Source identifier (zillow, mls, partner_api, etc)
        arv: After-repair value
        purchase_price: Initial purchase price
        payload: Additional data from source
    
    Returns:
        Created deal with id
    """
    if payload is None:
        payload = {}
    
    payload.update({
        "arv": arv,
        "purchase_price": purchase_price
    })
    
    result = create_deal(source=source, payload=payload)
    return {
        "success": True,
        "deal": result,
        "mode": "live" if is_live() else "sandbox"
    }


@intake_router.get("/deal/{deal_id}")
def get_deal_detail(deal_id: str):
    """Get deal detail by ID."""
    return {
        "deal_id": deal_id,
        "source": "unknown",
        "status": "pending"
    }
