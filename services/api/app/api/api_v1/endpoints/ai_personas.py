from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.ai_persona import AIPersona
from app.schemas.ai_persona import (
    AIPersonaCreate,
    AIPersonaUpdate,
    AIPersonaOut,
)

router = APIRouter()


@router.post("/", response_model=AIPersonaOut)
def create_ai_persona(
    payload: AIPersonaCreate,
    db: Session = Depends(get_db),
):
    existing = db.query(AIPersona).filter(
        (AIPersona.name == payload.name) | (AIPersona.code == payload.code)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Persona with that name/code already exists")
    obj = AIPersona(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[AIPersonaOut])
def list_ai_personas(
    domain: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(AIPersona)
    if domain:
        query = query.filter(AIPersona.domain == domain)
    if status:
        query = query.filter(AIPersona.status == status)
    return query.all()


@router.put("/{persona_id}", response_model=AIPersonaOut)
def update_ai_persona(
    persona_id: int,
    payload: AIPersonaUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(AIPersona).get(persona_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Persona not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
