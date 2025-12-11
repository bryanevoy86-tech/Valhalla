"""
PACK TZ: Config & Environment Registry Router
Prefix: /system/config
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.system_config import (
    SystemConfigSet,
    SystemConfigOut,
    SystemConfigList,
)
from app.services.system_config import (
    set_config,
    get_config,
    list_configs,
)

router = APIRouter(prefix="/system/config", tags=["System Config"])


@router.post("/", response_model=SystemConfigOut)
def set_config_endpoint(
    payload: SystemConfigSet,
    db: Session = Depends(get_db),
):
    return set_config(db, payload)


@router.get("/", response_model=SystemConfigList)
def list_configs_endpoint(
    db: Session = Depends(get_db),
):
    items = list_configs(db)
    return SystemConfigList(total=len(items), items=items)


@router.get("/{key}", response_model=SystemConfigOut)
def get_config_endpoint(
    key: str,
    db: Session = Depends(get_db),
):
    obj = get_config(db, key)
    if not obj:
        raise HTTPException(status_code=404, detail="Config key not found")
    return obj
