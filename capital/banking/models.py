"""
Data model – no secrets, no execution
"""

from enum import Enum
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AccountPurpose(str, Enum):
    OPERATING = "OPERATING"
    TAX = "TAX"
    RESERVE = "RESERVE"
    TRUST = "TRUST"
    DEAL_STAGING = "DEAL_STAGING"
    CREDIT = "CREDIT"


class BankAccount(BaseModel):
    id: str
    institution: str
    label: str
    account_type: str
    currency: str
    purpose: AccountPurpose
    masked_identifier: str  # last 4 digits only
    is_internal: bool
    created_at: datetime = datetime.utcnow()
    active: bool = True
