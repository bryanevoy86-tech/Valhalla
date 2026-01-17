from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from .schemas import BackupResult, BackupListResponse
from . import service

router = APIRouter(prefix="/core/export", tags=["core-export"])


@router.post("/backup", response_model=BackupResult)
def backup():
    return service.create_backup()


@router.get("/backups", response_model=BackupListResponse)
def backups(limit: int = Query(default=25, ge=1, le=200)):
    return {"items": service.list_backups(limit=limit)}


@router.get("/backup/{backup_id}", response_model=BackupResult)
def get_backup(backup_id: str):
    rec = service.get_backup(backup_id)
    if not rec:
        raise HTTPException(status_code=404, detail="backup not found")
    return rec


@router.get("/backup/{backup_id}/download")
def download_backup(backup_id: str):
    rec = service.get_backup(backup_id)
    if not rec:
        raise HTTPException(status_code=404, detail="backup not found")
    return FileResponse(path=rec["file_path"], filename=rec["file_name"], media_type="application/zip")
