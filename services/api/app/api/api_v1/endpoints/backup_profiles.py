from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.backup_profile import BackupProfile
from app.schemas.backup_profile import (
    BackupProfileCreate,
    BackupProfileUpdate,
    BackupProfileOut,
)

router = APIRouter()


@router.post("/", response_model=BackupProfileOut)
def create_backup_profile(
    payload: BackupProfileCreate,
    db: Session = Depends(get_db),
):
    obj = BackupProfile(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[BackupProfileOut])
def list_backup_profiles(
    db: Session = Depends(get_db),
):
    return db.query(BackupProfile).all()


@router.put("/{profile_id}", response_model=BackupProfileOut)
def update_backup_profile(
    profile_id: int,
    payload: BackupProfileUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(BackupProfile).get(profile_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
