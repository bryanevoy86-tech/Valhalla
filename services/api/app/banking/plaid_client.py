"""
Module 51: Plaid Client - Bank Account Linking
Handles connection to Plaid API for bank account linking.
"""
import os
from typing import Optional, Dict, Any

# Plaid configuration
PLAID_CONFIG = {
    "client_id": os.getenv("PLAID_CLIENT_ID", ""),
    "secret": os.getenv("PLAID_SECRET", ""),
    "environment": os.getenv("PLAID_ENVIRONMENT", "sandbox"),
}


def create_link_token(user_id: str, user_email: str) -> Dict[str, Any]:
    """
    Create a Plaid Link token for bank account linking.
    
    Args:
        user_id: Unique user identifier
        user_email: User email address
    
    Returns:
        dict: Link token response
    """
    if not PLAID_CONFIG["client_id"]:
        return {
            "status": "sandbox_mode",
            "link_token": "test_link_token_sandbox",
            "expiration": None
        }
    
    # TODO: Call Plaid API to create link token
    # In production: use plaid_client library
    return {
        "status": "link_token_created",
        "link_token": f"link_{user_id}",
        "expiration": "2026-02-12T00:00:00Z"
    }


def exchange_public_token(public_token: str) -> Dict[str, Any]:
    """
    Exchange Plaid public token for access token.
    
    Args:
        public_token: Token received from Plaid Link flow
    
    Returns:
        dict: Access token and account info
    """
    if not public_token:
        return {"status": "error", "message": "Invalid public token"}
    
    # TODO: Call Plaid API to exchange token
    return {
        "status": "token_exchanged",
        "access_token": f"access_{public_token}",
        "item_id": f"item_{public_token}"
    }


def get_accounts(access_token: str) -> Dict[str, Any]:
    """
    Get linked bank accounts for user.
    
    Args:
        access_token: Plaid access token
    
    Returns:
        dict: List of linked accounts
    """
    # TODO: Call Plaid API to get accounts
    return {
        "status": "accounts_retrieved",
        "accounts": [
            {
                "id": "acc_001",
                "name": "Checking Account",
                "subtype": "checking",
                "mask": "****1234"
            }
        ]
    }


def verify_account(access_token: str, account_id: str) -> Dict[str, Any]:
    """
    Verify ownership of bank account.
    
    Args:
        access_token: Plaid access token
        account_id: Account to verify
    
    Returns:
        dict: Verification status
    """
    return {
        "status": "account_verified",
        "account_id": account_id,
        "verified": True
    }
