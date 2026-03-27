from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...crud import file_asset as crud_files
from ...schemas.files import (
    FileOut,
    PresignDownloadOut,
    PresignUploadIn,
    PresignUploadOut,
    RegisterUploadIn,
)
from ...services.s3 import presign_get, presign_put
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/presign-upload", response_model=PresignUploadOut)
def presign_upload(payload: PresignUploadIn, user=Depends(get_current_user)):
    import re
    import secrets
    import time

    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", payload.filename).strip("_") or "file.bin"
    key = f"{payload.prefix or 'uploads'}/{payload.legacy_id or 'primary'}/{int(time.time())}-{secrets.token_hex(6)}-{safe_name}"
    url = presign_put(key, payload.content_type or "application/octet-stream")
    return PresignUploadOut(key=key, url=url)


@router.post("/register", response_model=FileOut)
def register_upload(
    payload: RegisterUploadIn, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    obj = crud_files.get_by_key(db, payload.key)
    if obj:
        obj.size = int(payload.size or 0)
        obj.content_type = payload.content_type or obj.content_type
        obj.filename = payload.filename or obj.filename
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    created = crud_files.create(
        db,
        key=payload.key,
        filename=payload.filename,
        content_type=payload.content_type or "application/octet-stream",
        size=int(payload.size or 0),
        legacy_id=payload.legacy_id or "primary",
        user_id=user.id,
    )
    return created


@router.get("", response_model=list[FileOut])
def list_files(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    legacy_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _ = user
    return crud_files.list_all(db, limit, offset, legacy_id)


@router.get("/{file_id}/presign-download", response_model=PresignDownloadOut)
def presign_download(file_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _ = user
    obj = crud_files.get_by_id(db, file_id)
    if not obj:
        raise HTTPException(status_code=404, detail="file not found")
    return PresignDownloadOut(url=presign_get(obj.key))
