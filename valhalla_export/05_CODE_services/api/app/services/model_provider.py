"""
PACK CL12: Model Provider Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.model_provider import ModelProvider
from app.schemas.model_provider import ModelProviderCreate


def create_model_provider(
    db: Session,
    payload: ModelProviderCreate,
) -> ModelProvider:
    # If this one is default_for_heimdall, clear that flag from others
    if payload.default_for_heimdall:
        db.query(ModelProvider).update({"default_for_heimdall": False})

    obj = ModelProvider(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_model_providers(db: Session) -> List[ModelProvider]:
    return db.query(ModelProvider).order_by(ModelProvider.created_at.desc()).all()


def get_default_heimdall_provider(db: Session) -> Optional[ModelProvider]:
    return (
        db.query(ModelProvider)
        .filter(ModelProvider.default_for_heimdall.is_(True))
        .first()
    )
