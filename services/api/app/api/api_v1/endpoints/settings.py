from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.global_setting import GlobalSetting
from app.schemas.settings import (
    GlobalSettingCreate,
    GlobalSettingUpdate,
    GlobalSettingOut,
)

router = APIRouter()


@router.post("/", response_model=GlobalSettingOut)
def create_setting(payload: GlobalSettingCreate, db: Session = Depends(get_db)):
    existing = db.query(GlobalSetting).filter(GlobalSetting.key == payload.key).first()
    if existing:
        raise HTTPException(status_code=400, detail="Key already exists")
    obj = GlobalSetting(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[GlobalSettingOut])
def list_settings(category: str | None = None, db: Session = Depends(get_db)):
    query = db.query(GlobalSetting)
    if category:
        query = query.filter(GlobalSetting.category == category)
    return query.all()


@router.get("/{key}", response_model=GlobalSettingOut)
def get_setting(key: str, db: Session = Depends(get_db)):
    obj = db.query(GlobalSetting).filter(GlobalSetting.key == key).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Setting not found")
    return obj


@router.put("/{key}", response_model=GlobalSettingOut)
def update_setting(key: str, payload: GlobalSettingUpdate, db: Session = Depends(get_db)):
    obj = db.query(GlobalSetting).filter(GlobalSetting.key == key).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Setting not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
