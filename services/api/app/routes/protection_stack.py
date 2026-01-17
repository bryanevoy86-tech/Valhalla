"""PACK 76: Protection Stack - Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.protection_stack import TrustEntityOut, TrustEntityCreate, ShieldModeOut, ShieldModeCreate
from app.services.protection_stack_service import (
    create_trust_entity, list_trust_entities, get_trust_entity, update_trust_entity, delete_trust_entity,
    set_shield_mode, get_latest_shield_mode, list_shield_modes, get_shield_mode, update_shield_mode, delete_shield_mode
)

router = APIRouter(prefix="/protection", tags=["protection_stack"])


# Trust entity endpoints
@router.post("/trust", response_model=TrustEntityOut)
def post_trust_entity(entity: TrustEntityCreate, db: Session = Depends(get_db)):
    return create_trust_entity(db, entity)


@router.get("/trusts", response_model=list[TrustEntityOut])
def get_trust_entities(db: Session = Depends(get_db)):
    return list_trust_entities(db)


@router.get("/trust/{entity_id}", response_model=TrustEntityOut)
def get_trust_entity_endpoint(entity_id: int, db: Session = Depends(get_db)):
    return get_trust_entity(db, entity_id)


@router.put("/trust/{entity_id}", response_model=TrustEntityOut)
def put_trust_entity(entity_id: int, entity: TrustEntityCreate, db: Session = Depends(get_db)):
    return update_trust_entity(db, entity_id, entity)


@router.delete("/trust/{entity_id}")
def delete_trust_entity_endpoint(entity_id: int, db: Session = Depends(get_db)):
    return delete_trust_entity(db, entity_id)


# Shield mode endpoints
@router.post("/shield", response_model=ShieldModeOut)
def post_shield_mode(shield: ShieldModeCreate, db: Session = Depends(get_db)):
    return set_shield_mode(db, shield)


@router.get("/shield/latest", response_model=ShieldModeOut | None)
def get_latest_shield_endpoint(db: Session = Depends(get_db)):
    return get_latest_shield_mode(db)


@router.get("/shields", response_model=list[ShieldModeOut])
def get_shield_modes_endpoint(db: Session = Depends(get_db)):
    return list_shield_modes(db)


@router.get("/shield/{shield_id}", response_model=ShieldModeOut)
def get_shield_mode_endpoint(shield_id: int, db: Session = Depends(get_db)):
    return get_shield_mode(db, shield_id)


@router.put("/shield/{shield_id}", response_model=ShieldModeOut)
def put_shield_mode(shield_id: int, shield: ShieldModeCreate, db: Session = Depends(get_db)):
    return update_shield_mode(db, shield_id, shield)


@router.delete("/shield/{shield_id}")
def delete_shield_mode_endpoint(shield_id: int, db: Session = Depends(get_db)):
    return delete_shield_mode(db, shield_id)
