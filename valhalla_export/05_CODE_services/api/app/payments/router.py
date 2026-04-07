"""
Module 55: Payment API Router
REST endpoints for payment processing.
"""
from fastapi import APIRouter, Request
from app.payments.service import charge, confirm_charge, get_charge_status

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/charge")
async def charge_customer(request: Request):
    """
    Charge a customer.
    
    Request body:
        {
            "amount": 50000,  # cents
            "customer_id": "cus_123",
            "method": "ach",
            "description": "Deal payment"
        }
    """
    try:
        data = await request.json()
        amount = data.get("amount")
        customer_id = data.get("customer_id")
        method = data.get("method", "ach")
        description = data.get("description")
        
        result = charge(
            amount_cents=amount,
            customer_id=customer_id,
            method=method,
            description=description
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


@router.post("/confirm")
async def confirm_payment(request: Request):
    """
    Confirm a pending payment.
    
    Request body:
        {
            "payment_id": "pi_123",
            "method": "ach"
        }
    """
    try:
        data = await request.json()
        payment_id = data.get("payment_id")
        method = data.get("method", "ach")
        
        result = confirm_charge(payment_id, method)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/status/{payment_id}")
def get_payment_status(payment_id: str, method: str = "ach"):
    """
    Get payment status.
    
    Args:
        payment_id: Payment ID
        method: Payment method
    """
    result = get_charge_status(payment_id, method)
    return {
        "status": "success",
        "data": result
    }
