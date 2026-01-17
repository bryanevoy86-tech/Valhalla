from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.closers.schemas import CloserCreate, CloserResponse
from app.closers.service import create_closer, get_closers


router = APIRouter(prefix="/ai-closers", tags=["ai-closers"])


@router.post("/", response_model=CloserResponse)
def create_closer_route(closer: CloserCreate, db: Session = Depends(get_db)):
    return create_closer(db=db, closer=closer)


@router.get("/", response_model=List[CloserResponse])
def list_all_closers(db: Session = Depends(get_db)):
    return get_closers(db=db)
