from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.queen_stream import QueenStream
from app.schemas.queen import QueenStreamCreate, QueenStreamUpdate, QueenStreamOut

router = APIRouter()

@router.post("/", response_model=QueenStreamOut)
def create_queen_stream(payload: QueenStreamCreate, db: Session = Depends(get_db)):
    obj = QueenStream(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/", response_model=list[QueenStreamOut])
def list_queen_streams(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(QueenStream)
    if status:
        query = query.filter(QueenStream.status == status)
    return query.all()

@router.put("/{stream_id}", response_model=QueenStreamOut)
def update_queen_stream(stream_id: int, payload: QueenStreamUpdate, db: Session = Depends(get_db)):
    obj = db.query(QueenStream).get(stream_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
