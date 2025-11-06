from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.knowledge.schemas import KnowledgeCreate, KnowledgeResponse
from app.knowledge.service import ingest, list_fresh, purge_expired


router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/", response_model=KnowledgeResponse)
def ingest_doc(doc: KnowledgeCreate, db: Session = Depends(get_db)):
    return ingest(db, doc)


@router.get("/", response_model=List[KnowledgeResponse])
def fresh_docs(tag: Optional[str] = None, db: Session = Depends(get_db)):
    return list_fresh(db, tag)


@router.post("/purge", response_model=int)
def purge(db: Session = Depends(get_db)):
    return purge_expired(db)
