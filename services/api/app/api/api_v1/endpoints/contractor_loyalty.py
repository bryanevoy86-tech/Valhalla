from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.contractor_loyalty import ContractorRank, ContractorLoyaltyVault
from app.schemas.contractor_loyalty import (
    ContractorRankCreate,
    ContractorRankOut,
    ContractorLoyaltyVaultCreate,
    ContractorLoyaltyVaultUpdate,
    ContractorLoyaltyVaultOut,
)

router = APIRouter()


@router.post("/ranks", response_model=ContractorRankOut)
def create_contractor_rank(payload: ContractorRankCreate, db: Session = Depends(get_db)):
    obj = ContractorRank(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/ranks", response_model=list[ContractorRankOut])
def list_contractor_ranks(db: Session = Depends(get_db)):
    return db.query(ContractorRank).all()


@router.post("/vaults", response_model=ContractorLoyaltyVaultOut)
def create_contractor_vault(payload: ContractorLoyaltyVaultCreate, db: Session = Depends(get_db)):
    obj = ContractorLoyaltyVault(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/vaults", response_model=list[ContractorLoyaltyVaultOut])
def list_contractor_vaults(
    contractor_id: int | None = None,
    rank_code: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ContractorLoyaltyVault)
    if contractor_id is not None:
        query = query.filter(ContractorLoyaltyVault.contractor_id == contractor_id)
    if rank_code:
        query = query.filter(ContractorLoyaltyVault.rank_code == rank_code)
    return query.all()


@router.put("/vaults/{vault_id}", response_model=ContractorLoyaltyVaultOut)
def update_contractor_vault(vault_id: int, payload: ContractorLoyaltyVaultUpdate, db: Session = Depends(get_db)):
    obj = db.query(ContractorLoyaltyVault).get(vault_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
