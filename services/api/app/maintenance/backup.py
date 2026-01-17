# app/maintenance/backup.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

# Later, Heimdall will wire this into real S3/Backblaze/Render backups, etc.

class SnapshotRequest(BaseModel):
    reason: str
    include_database: bool = True
    include_configs: bool = True
    triggered_by: str = "system"

class SnapshotRecord(BaseModel):
    id: str
    created_at: datetime
    status: str
    location: Optional[str] = None
    size_mb: Optional[float] = None
    reason: Optional[str] = None

class BackupService:
    @staticmethod
    async def create_snapshot(request: SnapshotRequest) -> SnapshotRecord:
        # TODO: replace with actual backup logic (pg_dump, config export, etc.)
        now = datetime.utcnow()
        snapshot_id = f"snapshot-{now.strftime('%Y%m%d-%H%M%S')}"
        return SnapshotRecord(
            id=snapshot_id,
            created_at=now,
            status="scheduled",
            location=None,
            size_mb=None,
            reason=request.reason,
        )

    @staticmethod
    async def list_snapshots() -> list[SnapshotRecord]:
        # TODO: later: pull from telemetry_events or a dedicated table
        return []
