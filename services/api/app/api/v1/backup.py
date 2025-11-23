# app/api/v1/backup.py
from fastapi import APIRouter, Depends
from typing import List

from app.auth.dependencies import get_current_admin_user  # reuse existing guard
from app.maintenance.backup import BackupService, SnapshotRequest, SnapshotRecord

router = APIRouter(prefix="/backup", tags=["backup"])

@router.post("/snapshots", response_model=SnapshotRecord)
async def create_snapshot(
    payload: SnapshotRequest,
    user=Depends(get_current_admin_user),
):
    # Heimdall can call this internally too, but we require admin user for UI calls.
    return await BackupService.create_snapshot(payload)

@router.get("/snapshots", response_model=List[SnapshotRecord])
async def list_snapshots(user=Depends(get_current_admin_user)):
    return await BackupService.list_snapshots()
