from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.material_item import MaterialItem
from app.schemas.materials import (
    MaterialItemCreate,
    MaterialItemUpdate,
    MaterialItemOut,
)

router = APIRouter()

@router.post("/", response_model=MaterialItemOut)
def create_material(
    payload: MaterialItemCreate,
    db: Session = Depends(get_db),
):
    obj = MaterialItem(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/", response_model=list[MaterialItemOut])
def list_materials(
    category: str | None = None,
    region: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(MaterialItem)
    if category:
        query = query.filter(MaterialItem.category == category)
    if region:
        query = query.filter(MaterialItem.region == region)
    return query.all()

@router.put("/{material_id}", response_model=MaterialItemOut)
def update_material(
    material_id: int,
    payload: MaterialItemUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(MaterialItem).get(material_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
