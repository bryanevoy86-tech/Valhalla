from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.finops.schemas import (
    BankConnectionCreate,
    BankConnectionResponse,
    BankAccountCreate,
    BankAccountResponse,
    ESignCreate,
    ESignResponse,
    VaultBalanceUpsert,
    VaultBalanceResponse,
)
from app.finops.service import (
    create_connection,
    list_connections,
    add_account,
    list_accounts,
    update_balance,
    create_envelope,
    list_envelopes,
    mark_envelope_status,
    upsert_vault,
    list_vaults,
)


router = APIRouter(prefix="/finops", tags=["finops"])


# Banking
@router.post("/connections", response_model=BankConnectionResponse)
def new_connection(payload: BankConnectionCreate, db: Session = Depends(get_db)):
    return create_connection(db, payload)


@router.get("/connections", response_model=List[BankConnectionResponse])
def connections(db: Session = Depends(get_db)):
    return list_connections(db)


@router.post("/accounts", response_model=BankAccountResponse)
def new_account(payload: BankAccountCreate, db: Session = Depends(get_db)):
    return add_account(db, payload)


@router.get("/accounts", response_model=List[BankAccountResponse])
def accounts(connection_id: Optional[int] = None, db: Session = Depends(get_db)):
    return list_accounts(db, connection_id)


@router.post("/accounts/{account_id}/balance", response_model=BankAccountResponse)
def set_balance(account_id: int, balance: float, db: Session = Depends(get_db)):
    acct = update_balance(db, account_id, balance)
    if not acct:
        raise HTTPException(status_code=404, detail="Account not found")
    return acct


# E-Sign
@router.post("/esign", response_model=ESignResponse)
def create_esign(payload: ESignCreate, db: Session = Depends(get_db)):
    return create_envelope(db, payload)


@router.get("/esign", response_model=List[ESignResponse])
def all_esign(db: Session = Depends(get_db)):
    return list_envelopes(db)


@router.post("/esign/{env_id}/status", response_model=ESignResponse)
def esign_status(env_id: int, status: str, db: Session = Depends(get_db)):
    env = mark_envelope_status(db, env_id, status)
    if not env:
        raise HTTPException(status_code=404, detail="Envelope not found")
    return env


# Vault Sync
@router.post("/vaults", response_model=VaultBalanceResponse)
def upsert(payload: VaultBalanceUpsert, db: Session = Depends(get_db)):
    return upsert_vault(db, payload)


@router.get("/vaults", response_model=List[VaultBalanceResponse])
def vaults(db: Session = Depends(get_db)):
    return list_vaults(db)
