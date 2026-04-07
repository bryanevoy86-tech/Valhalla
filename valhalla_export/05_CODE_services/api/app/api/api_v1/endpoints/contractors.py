from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.contractor import Contractor
from app.schemas.contractor import ContractorCreate, ContractorUpdate, ContractorOut

router = APIRouter()

@router.post("/", response_model=ContractorOut)
def create_contractor(payload: ContractorCreate, db: Session = Depends(get_db)):
    obj = Contractor(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/", response_model=list[ContractorOut])
def list_contractors(db: Session = Depends(get_db)):
    return db.query(Contractor).all()

@router.put("/{contractor_id}", response_model=ContractorOut)
def update_contractor(contractor_id: int, payload: ContractorUpdate, db: Session = Depends(get_db)):
    obj = db.query(Contractor).get(contractor_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
