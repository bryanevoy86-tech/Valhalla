"""PACK-CORE-PRELAUNCH-01: Bootloader - Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db

from . import schemas, service

router = APIRouter(prefix="/bootloader", tags=["bootloader"])


@router.post("/run", response_model=schemas.BootLogRead)
def run_boot(db: Session = Depends(get_db)):
    log = service.run_boot_sequence(db)
    return schemas.BootLogRead.model_validate(log)


@router.get("/last", response_model=schemas.BootLogRead | None)
def get_last(db: Session = Depends(get_db)):
    log = service.get_last_boot(db)
    return schemas.BootLogRead.model_validate(log) if log else None
