"""
Heimdall intake logic – fills everything for you
"""

import uuid
from .models import BankAccount, AccountPurpose
from .registry import register_account


def heimdall_bank_intake(
    institution: str,
    label: str,
    account_type: str,
    currency: str,
    purpose: AccountPurpose,
    masked_identifier: str,
    is_internal: bool,
):
    """
    Heimdall-driven bank account intake.
    
    Creates a BankAccount, registers it, and returns it.
    No secrets stored, only masked identifiers.
    """
    account = BankAccount(
        id=str(uuid.uuid4()),
        institution=institution,
        label=label,
        account_type=account_type,
        currency=currency,
        purpose=purpose,
        masked_identifier=masked_identifier,
        is_internal=is_internal,
    )
    register_account(account)
    return account
