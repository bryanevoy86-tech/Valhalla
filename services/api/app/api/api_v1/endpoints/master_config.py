from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.master_config import MasterConfig
from app.schemas.master_config import (
    MasterConfigCreate,
    MasterConfigUpdate,
    MasterConfigOut,
)

router = APIRouter()


@router.post("/", response_model=MasterConfigOut)
def create_master_config(
    payload: MasterConfigCreate,
    db: Session = Depends(get_db),
):
    obj = MasterConfig(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[MasterConfigOut])
def list_master_config(
    prefix: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(MasterConfig)
    if prefix:
        query = query.filter(MasterConfig.config_key.like(f"{prefix}%"))
    return query.order_by(MasterConfig.config_key.asc()).all()


@router.get("/{config_key}", response_model=MasterConfigOut)
def get_config(
    config_key: str,
    db: Session = Depends(get_db),
):
    obj = db.query(MasterConfig).filter(MasterConfig.config_key == config_key).first()
    return obj


@router.put("/{config_key}", response_model=MasterConfigOut)
def update_config(
    config_key: str,
    payload: MasterConfigUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(MasterConfig).filter(MasterConfig.config_key == config_key).first()
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
