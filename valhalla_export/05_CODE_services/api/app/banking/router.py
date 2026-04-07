"""
Module 52: Bank Account Link Endpoint
REST API for bank account linking and management.
"""
from fastapi import APIRouter, Request
from app.banking.plaid_client import (
    create_link_token,
    exchange_public_token,
    get_accounts,
    verify_account
)

router = APIRouter(prefix="/banking", tags=["banking"])


@router.post("/link/create")
async def create_link(request: Request):
    """
    Create a Plaid Link token to start bank linking.
    
    Request body:
        {
            "user_id": "user_123",
            "user_email": "user@example.com"
        }
    """
    try:
        data = await request.json()
        user_id = data.get("user_id")
        user_email = data.get("user_email")
        
        result = create_link_token(user_id, user_email)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/link/exchange")
async def exchange_token(request: Request):
    """
    Exchange Plaid public token for access token.
    
    Request body:
        {
            "public_token": "public_xxx"
        }
    """
    try:
        data = await request.json()
        public_token = data.get("public_token")
        
        result = exchange_public_token(public_token)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/accounts/{access_token}")
def get_linked_accounts(access_token: str):
    """
    Get list of linked bank accounts.
    
    Args:
        access_token: Plaid access token
    """
    result = get_accounts(access_token)
    return {
        "status": "success",
        "data": result
    }


@router.post("/verify")
async def verify_bank_account(request: Request):
    """
    Verify ownership of bank account.
    
    Request body:
        {
            "access_token": "access_xxx",
            "account_id": "acc_001"
        }
    """
    try:
        data = await request.json()
        access_token = data.get("access_token")
        account_id = data.get("account_id")
        
        result = verify_account(access_token, account_id)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
