from fastapi import APIRouter, Depends
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
    obj = AIPersona(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[AIPersonaOut])
def list_ai_personas(
    active: bool | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(AIPersona)
    if active is not None:
        query = query.filter(AIPersona.active == active)
    return query.order_by(AIPersona.name.asc()).all()


@router.put("/{persona_id}", response_model=AIPersonaOut)
def update_ai_persona(
    persona_id: int,
    payload: AIPersonaUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(AIPersona).get(persona_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
