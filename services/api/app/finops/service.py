from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.finops.models import BankConnection, BankAccount, ESignEnvelope, VaultBalance
from app.finops.schemas import (
    BankConnectionCreate,
    BankAccountCreate,
    ESignCreate,
    VaultBalanceUpsert,
)


# BANKING
def create_connection(db: Session, payload: BankConnectionCreate) -> BankConnection:
    conn = BankConnection(
        provider=payload.provider,
        access_token=payload.access_token,
        status="connected" if payload.access_token else "disconnected",
        meta=payload.meta,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


def list_connections(db: Session) -> List[BankConnection]:
    return db.query(BankConnection).all()


def add_account(db: Session, payload: BankAccountCreate) -> BankAccount:
    acct = BankAccount(**payload.dict())
    db.add(acct)
    db.commit()
    db.refresh(acct)
    return acct


def list_accounts(
    db: Session, connection_id: Optional[int] = None
) -> List[BankAccount]:
    q = db.query(BankAccount)
    if connection_id:
        q = q.filter(BankAccount.connection_id == connection_id)
    return q.all()


def update_balance(
    db: Session, account_id: int, balance: float
) -> Optional[BankAccount]:
    acct = db.get(BankAccount, account_id)
    if not acct:
        return None
    acct.balance = balance
    db.commit()
    db.refresh(acct)
    return acct


# E-SIGN
def create_envelope(db: Session, payload: ESignCreate) -> ESignEnvelope:
    env = ESignEnvelope(
        provider=payload.provider,
        subject=payload.subject,
        recipients=[r.dict() for r in payload.recipients],
        status="created",
        meta=payload.meta,
    )
    db.add(env)
    db.commit()
    db.refresh(env)
    return env


def mark_envelope_status(
    db: Session, env_id: int, status: str
) -> Optional[ESignEnvelope]:
    env = db.get(ESignEnvelope, env_id)
    if not env:
        return None
    env.status = status
    db.commit()
    db.refresh(env)
    return env


def list_envelopes(db: Session) -> List[ESignEnvelope]:
    return db.query(ESignEnvelope).order_by(ESignEnvelope.id.desc()).all()


# VAULT SYNC
def upsert_vault(db: Session, payload: VaultBalanceUpsert) -> VaultBalance:
    vb = (
        db.query(VaultBalance)
        .filter(
            VaultBalance.vault_code == payload.vault_code,
            VaultBalance.currency == payload.currency,
        )
        .first()
    )
    if not vb:
        vb = VaultBalance(
            vault_code=payload.vault_code,
            currency=payload.currency,
            balance=payload.balance,
            last_source=payload.last_source,
        )
        db.add(vb)
    else:
        vb.balance = payload.balance
        vb.last_source = payload.last_source
        vb.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(vb)
    return vb


def list_vaults(db: Session) -> List[VaultBalance]:
    return db.query(VaultBalance).all()
