from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from app.security.service import EncryptionService
from app.security.schemas import EncryptedData
from app.core.db import get_db


router = APIRouter(prefix="/encryption", tags=["encryption"])


@router.post("/encrypt", response_model=EncryptedData)
async def encrypt_data(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    data = payload.get("data")
    if not data:
        data = ""
    key = EncryptionService.generate_encryption_key()
    return EncryptionService(db).encrypt_data(data, key)


@router.post("/decrypt", response_model=str)
async def decrypt_data(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    encrypted_data = payload.get("encrypted_data") or ""
    encryption_key = payload.get("encryption_key") or ""
    return EncryptionService(db).decrypt_data(encrypted_data, encryption_key)
