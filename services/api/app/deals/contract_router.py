"""
Module 74: Auto-Contract Router
FastAPI endpoints to automatically create contracts from leads.
"""
from fastapi import APIRouter
from app.deals.contract_packager import package_for_contract
from app.contracts.flow import start_contract


router = APIRouter(prefix="/deals", tags=["Deals"])


@router.post("/lead-to-contract")
def lead_to_contract(payload: dict):
    """
    Create contract from deal lead (auto).
    
    Pipeline: Lead → Offer → Contract
    
    Args:
        payload: Lead data dict
            {
                "address": "123 Main St",
                "city": "Denver",
                "state": "CO",
                "asking_price": 250000,
                "arv": 350000,
                "repairs": 30000
            }
    
    Returns:
        dict: Packaged deal and contract result
    """
    try:
        packaged = package_for_contract(payload)
        if not packaged["ok"]:
            return {"ok": False, "packaged": packaged}

        # party is placeholder until you wire identity/CRM
        contract = start_contract(packaged["template"], party_name="seller", party_email="seller@example.com", contract_data=packaged["merge_data"])
        return {"ok": True, "packaged": packaged, "contract": contract}
    except Exception as e:
        return {"ok": False, "error": str(e)}
