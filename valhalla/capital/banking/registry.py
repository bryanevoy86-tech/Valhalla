"""
Account registry + whitelist
"""

from typing import Dict
from .models import BankAccount

BANK_ACCOUNT_REGISTRY: Dict[str, BankAccount] = {}
INTERNAL_WHITELIST = set()


def register_account(account: BankAccount):
    """Register a bank account in the registry."""
    BANK_ACCOUNT_REGISTRY[account.id] = account
    if account.is_internal:
        INTERNAL_WHITELIST.add(account.id)


def get_account(account_id: str) -> BankAccount:
    """Get a bank account by ID."""
    return BANK_ACCOUNT_REGISTRY[account_id]
