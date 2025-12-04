from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.governance_settings import GovernanceSettings
from app.schemas.governance_settings import (
    GovernanceSettingsCreate,
    GovernanceSettingsUpdate,
    GovernanceSettingsOut,
)

router = APIRouter()


@router.post("/", response_model=GovernanceSettingsOut)
def create_governance_settings(
    payload: GovernanceSettingsCreate,
    db: Session = Depends(get_db),
):
    obj = GovernanceSettings(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[GovernanceSettingsOut])
def list_governance_settings(db: Session = Depends(get_db)):
    return db.query(GovernanceSettings).all()


@router.put("/{settings_id}", response_model=GovernanceSettingsOut)
def update_governance_settings(
    settings_id: int,
    payload: GovernanceSettingsUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(GovernanceSettings).get(settings_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
