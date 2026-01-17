"""
PACK UD: API Key & Client Registry Service
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.api_clients import ApiClient
from app.schemas.api_clients import ApiClientCreate


def create_api_client(
    db: Session,
    payload: ApiClientCreate,
) -> ApiClient:
    obj = ApiClient(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_api_clients(db: Session) -> List[ApiClient]:
    return db.query(ApiClient).order_by(ApiClient.created_at.desc()).all()


def get_api_client_by_key(db: Session, api_key: str) -> Optional[ApiClient]:
    return (
        db.query(ApiClient)
        .filter(ApiClient.api_key == api_key, ApiClient.active.is_(True))
        .first()
    )


def set_api_client_active(
    db: Session,
    client_id: int,
    active: bool,
) -> Optional[ApiClient]:
    obj = db.query(ApiClient).filter(ApiClient.id == client_id).first()
    if not obj:
        return None
    obj.active = active
    obj.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return obj
