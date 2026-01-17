from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.knowledge_source import KnowledgeSource
from app.schemas.knowledge_source import (
    KnowledgeSourceCreate,
    KnowledgeSourceUpdate,
    KnowledgeSourceOut,
)

router = APIRouter()


@router.post("/", response_model=KnowledgeSourceOut)
def create_knowledge_source(payload: KnowledgeSourceCreate, db: Session = Depends(get_db)):
    obj = KnowledgeSource(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[KnowledgeSourceOut])
def list_knowledge_sources(
    category: str | None = None,
    engine: str | None = None,
    active: bool | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(KnowledgeSource)
    if category:
        query = query.filter(KnowledgeSource.category == category)
    if engine:
        query = query.filter(KnowledgeSource.engines.contains(engine))
    if active is not None:
        query = query.filter(KnowledgeSource.active == active)
    return query.order_by(KnowledgeSource.priority.asc()).all()


@router.put("/{source_id}", response_model=KnowledgeSourceOut)
def update_knowledge_source(source_id: int, payload: KnowledgeSourceUpdate, db: Session = Depends(get_db)):
    obj = db.query(KnowledgeSource).get(source_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
