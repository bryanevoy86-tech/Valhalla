from pydantic import BaseModel
from typing import Optional, Dict, Any, List


# Banking
class BankConnectionCreate(BaseModel):
    provider: str
    access_token: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class BankConnectionResponse(BankConnectionCreate):
    id: int
    status: str

    class Config:
        from_attributes = True


class BankAccountCreate(BaseModel):
    connection_id: int
    name: str
    mask: Optional[str] = None
    currency: str = "CAD"
    balance: float = 0.0
    type: str = "checking"


class BankAccountResponse(BankAccountCreate):
    id: int
    active: bool

    class Config:
        from_attributes = True


# E-Sign
class Recipient(BaseModel):
    email: str
    name: str


class ESignCreate(BaseModel):
    provider: str
    subject: str
    recipients: List[Recipient]
    meta: Optional[Dict[str, Any]] = None


class ESignResponse(ESignCreate):
    id: int
    status: str

    class Config:
        from_attributes = True


# Vaults
class VaultBalanceUpsert(BaseModel):
    vault_code: str
    currency: str = "CAD"
    balance: float
    last_source: Optional[str] = None


class VaultBalanceResponse(VaultBalanceUpsert):
    id: int

    class Config:
        from_attributes = True
