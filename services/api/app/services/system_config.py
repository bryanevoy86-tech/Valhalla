"""
PACK TZ: Config & Environment Registry Service
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.system_config import SystemConfig
from app.schemas.system_config import SystemConfigSet


def set_config(
    db: Session,
    payload: SystemConfigSet,
) -> SystemConfig:
    obj = (
        db.query(SystemConfig)
        .filter(SystemConfig.key == payload.key)
        .first()
    )
    if not obj:
        obj = SystemConfig(
            key=payload.key,
            value=payload.value,
            description=payload.description,
            mutable=payload.mutable,
        )
        db.add(obj)
    else:
        if not obj.mutable and payload.value is not None:
            # Immutable values can't be changed
            return obj
        if payload.value is not None:
            obj.value = payload.value
        if payload.description is not None:
            obj.description = payload.description
        obj.mutable = payload.mutable

    obj.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return obj


def get_config(
    db: Session,
    key: str,
) -> Optional[SystemConfig]:
    return (
        db.query(SystemConfig)
        .filter(SystemConfig.key == key)
        .first()
    )


def list_configs(db: Session) -> List[SystemConfig]:
    return (
        db.query(SystemConfig)
        .order_by(SystemConfig.key.asc())
        .all()
    )
