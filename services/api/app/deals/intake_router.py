"""
Module 70: Lead Intake Router
FastAPI endpoints for deal lead intake.
"""
from fastapi import APIRouter
from app.deals.intake_store import LEADS


router = APIRouter(prefix="/deals", tags=["Deals"])


@router.post("/intake")
def intake(payload: dict):
    """
    Submit new deal lead for intake.
    
    Args:
        payload: Lead data dict
            {
                "source": "direct",
                "address": "123 Main St",
                "city": "Denver",
                "state": "CO",
                "asking_price": 250000,
                "arv": 350000,
                "repairs": 30000
            }
    
    Returns:
        dict: Success status and created lead
    """
    try:
        lead = LEADS.create(payload)
        return {"ok": True, "lead": lead}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/leads")
def list_leads():
    """
    List all deal leads.
    
    Returns:
        dict: Success status and list of leads
    """
    try:
        return {"ok": True, "leads": LEADS.list()}
    except Exception as e:
        return {"ok": False, "error": str(e)}
