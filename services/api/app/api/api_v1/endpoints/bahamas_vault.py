from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.bahamas_vault import BahamasVault
from app.schemas.bahamas_vault import (
    BahamasVaultCreate,
    BahamasVaultUpdate,
    BahamasVaultOut,
)

router = APIRouter()


@router.post("/", response_model=BahamasVaultOut)
def create_bahamas_vault(payload: BahamasVaultCreate, db: Session = Depends(get_db)):
    obj = BahamasVault(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[BahamasVaultOut])
def list_bahamas_vaults(db: Session = Depends(get_db)):
    return db.query(BahamasVault).all()


@router.put("/{vault_id}", response_model=BahamasVaultOut)
def update_bahamas_vault(vault_id: int, payload: BahamasVaultUpdate, db: Session = Depends(get_db)):
    obj = db.query(BahamasVault).get(vault_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
