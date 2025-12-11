"""
PACK CL12: Model Provider Router
Prefix: /system/models
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.model_provider import (
    ModelProviderCreate,
    ModelProviderOut,
    ModelProviderList,
)
from app.services.model_provider import (
    create_model_provider,
    list_model_providers,
    get_default_heimdall_provider,
)

router = APIRouter(
    prefix="/system/models",
    tags=["System", "Models"],
)


@router.post("/", response_model=ModelProviderOut, status_code=201)
def register_model_provider(
    payload: ModelProviderCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new AI model provider that Heimdall can use.
    """
    obj = create_model_provider(db, payload)
    return obj


@router.get("/", response_model=ModelProviderList)
def get_model_providers(
    db: Session = Depends(get_db),
):
    items = list_model_providers(db)
    return ModelProviderList(
        total=len(items),
        items=[ModelProviderOut.model_validate(i) for i in items],
    )


@router.get("/default", response_model=ModelProviderOut | None)
def get_default_model_for_heimdall(
    db: Session = Depends(get_db),
):
    """
    Get the model provider Heimdall should use by default.
    """
    provider = get_default_heimdall_provider(db)
    if provider is None:
        return None
    return ModelProviderOut.model_validate(provider)
