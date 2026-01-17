from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.trust import Trust
from app.schemas.trust import TrustCreate, TrustUpdate, TrustOut

router = APIRouter()

@router.post("/", response_model=TrustOut)
def create_trust(payload: TrustCreate, db: Session = Depends(get_db)):
    obj = Trust(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/", response_model=list[TrustOut])
def list_trusts(db: Session = Depends(get_db)):
    return db.query(Trust).all()

@router.put("/{trust_id}", response_model=TrustOut)
def update_trust(trust_id: int, payload: TrustUpdate, db: Session = Depends(get_db)):
    obj = db.query(Trust).get(trust_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
