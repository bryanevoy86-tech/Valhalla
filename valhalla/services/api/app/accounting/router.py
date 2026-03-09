"""
Module 58: Accounting Router
REST endpoints for accounting operations.
"""
from fastapi import APIRouter, Request
from app.accounting.sync import sync_revenue, sync_fees, get_account_balance

router = APIRouter(prefix="/accounting", tags=["accounting"])


@router.post("/sync/revenue")
async def sync_revenue_endpoint(request: Request):
    """
    Sync revenue to QuickBooks.
    
    Request body:
        {
            "amount": 50000,  # cents
            "source": "deal",
            "customer_name": "John Doe",
            "deal_id": "deal_123"
        }
    """
    try:
        data = await request.json()
        amount = data.get("amount")
        source = data.get("source")
        customer_name = data.get("customer_name")
        deal_id = data.get("deal_id")
        
        result = sync_revenue(
            amount_cents=amount,
            source=source,
            customer_name=customer_name,
            deal_id=deal_id
        )
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/sync/fees")
async def sync_fees_endpoint(request: Request):
    """
    Sync fees to QuickBooks.
    
    Request body:
        {
            "amount": 5000,  # cents
            "fee_type": "arbitrage",
            "deal_id": "deal_123"
        }
    """
    try:
        data = await request.json()
        amount = data.get("amount")
        fee_type = data.get("fee_type")
        deal_id = data.get("deal_id")
        
        result = sync_fees(
            amount_cents=amount,
            fee_type=fee_type,
            deal_id=deal_id
        )
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/balance/{account_number}")
def get_balance(account_number: str):
    """
    Get QuickBooks account balance.
    
    Args:
        account_number: GL account number
    """
    result = get_account_balance(account_number)
    return {
        "status": "success",
        "data": result
    }
