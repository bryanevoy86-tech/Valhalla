from __future__ import annotations

import os

from backend.storage.factory import get_storage
from backend.storage.util import build_key
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

router = APIRouter(prefix="/files", tags=["files"])


def _ensure_allowed_content_type(ct: str):
    # keep simple for now; tighten later
    if not ct:
        raise HTTPException(400, "Missing content_type")
    return ct


@router.get("/upload-url")
async def get_upload_url(
    org_id: int = Query(..., ge=1),
    filename: str = Query(..., min_length=1),
    content_type: str = Query(..., min_length=3),
    expires_in: int = Query(3600, ge=60, le=24 * 3600),
):
    storage = get_storage()
    key = build_key(
        base_prefix=os.getenv("STORAGE_BASE_PREFIX", "uploads"), org_id=org_id, filename=filename
    )
    _ensure_allowed_content_type(content_type)
    spec = await storage.generate_upload_url(
        key=key, content_type=content_type, expires_in=expires_in
    )
    # also hand back a download url _template_ (client can hit after upload)
    download_url = await storage.generate_download_url(key, expires_in=expires_in)
    return {"upload": spec, "download_url": download_url, "key": key}


@router.post("/upload")
async def upload_local(
    key: str = Form(...),
    content_type: str = Form(...),
    file: UploadFile = File(...),
):
    # Only used for local backend. You may optionally guard by env.
    from backend.storage.local import LocalStorage

    storage = LocalStorage()
    data = await file.read()
    dest = (storage.UPLOAD_ROOT / key).resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        f.write(data)

    # Scan after saving
    from backend.security.malware_scan import scan_file

    clean, msg = await scan_file(str(dest))
    if not clean:
        os.remove(dest)
        raise HTTPException(400, f"Malware detected: {msg}")

    dl = await storage.generate_download_url(f"uploads/{key}")
    return {"ok": True, "download_url": dl, "key": f"uploads/{key}", "scan": msg}
