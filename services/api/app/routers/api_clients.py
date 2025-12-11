"""
PACK UD: API Key & Client Registry Router
Prefix: /system/clients
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.api_clients import ApiClientCreate, ApiClientOut, ApiClientList
from app.services.api_clients import (
    create_api_client,
    list_api_clients,
    set_api_client_active,
)

router = APIRouter(prefix="/system/clients", tags=["API Clients"])


@router.post("/", response_model=ApiClientOut)
def create_client_endpoint(
    payload: ApiClientCreate,
    db: Session = Depends(get_db),
):
    return create_api_client(db, payload)


@router.get("/", response_model=ApiClientList)
def list_clients_endpoint(
    db: Session = Depends(get_db),
):
    items = list_api_clients(db)
    return ApiClientList(total=len(items), items=items)


@router.post("/{client_id}/activate", response_model=ApiClientOut)
def activate_client_endpoint(
    client_id: int,
    db: Session = Depends(get_db),
):
    obj = set_api_client_active(db, client_id, True)
    if not obj:
        raise HTTPException(status_code=404, detail="Client not found")
    return obj


@router.post("/{client_id}/deactivate", response_model=ApiClientOut)
def deactivate_client_endpoint(
    client_id: int,
    db: Session = Depends(get_db),
):
    obj = set_api_client_active(db, client_id, False)
    if not obj:
        raise HTTPException(status_code=404, detail="Client not found")
    return obj
