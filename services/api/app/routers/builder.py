import json, os
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from slugify import slugify

from ..core.db import get_db
from ..core.settings import settings
from ..core.dependencies import require_builder_key
from ..models.builder import BuilderTask, BuilderEvent
from ..schemas.builder import (
    RegisterIn, RegisterOut, TaskIn, TaskOut, DraftOut, FileSpec, TelemetryIn, ApplyIn
)

router = APIRouter(prefix="/builder", tags=["builder"])

def _path_is_allowed(path: str) -> bool:
    norm = path.replace("\\", "/").strip().lstrip("./")
    return any(norm.startswith(d + "/") or norm == d for d in settings.BUILDER_ALLOWED_DIRS)

@router.post("/register", response_model=RegisterOut)
def register(payload: RegisterIn, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    db.add(BuilderEvent(kind="register", msg=payload.agent_name, meta_json=payload.version or ""))
    db.commit()
    return RegisterOut(ok=True, message=f"Welcome, {payload.agent_name}.")

@router.get("/tasks", response_model=List[TaskOut])
def list_tasks(db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    rows = db.query(BuilderTask).order_by(BuilderTask.id.desc()).limit(50).all()
    return [TaskOut(id=r.id, title=r.title, scope=r.scope, status=r.status, diff_summary=r.diff_summary) for r in rows]

@router.post("/tasks", response_model=DraftOut)
def create_task(payload: TaskIn, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    # Heimdall will later POST /apply with files; for now create placeholder
    t = BuilderTask(title=payload.title, scope=payload.scope, status="queued", plan=payload.plan or "")
    db.add(t); db.commit(); db.refresh(t)
    # Empty draft (Heimdall will update via /apply with approve=false first)
    return DraftOut(task_id=t.id, files=[], diff_summary="queued")

@router.post("/apply", response_model=DraftOut)
def apply(payload: ApplyIn, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    t = db.get(BuilderTask, payload.task_id)
    if not t:
        raise HTTPException(status_code=404, detail="task not found")

    # The last proposed files live in payload_json; on approve we write to disk.
    try:
        proposed = json.loads(t.payload_json or "[]")
    except json.JSONDecodeError:
        proposed = []

    if not payload.approve:
        # return current draft (human review)
        return DraftOut(task_id=t.id, files=proposed, diff_summary=t.diff_summary or "")

    # Guardrails: write allowed files only
    wrote = []
    for f in proposed:
        path = f["path"].strip()
        content = f["content"]
        mode = f.get("mode", "add")
        if not _path_is_allowed(path):
            raise HTTPException(status_code=400, detail=f"path not allowed: {path}")
        if len(content.encode("utf-8")) > settings.BUILDER_MAX_FILE_BYTES:
            raise HTTPException(status_code=413, detail=f"file too large: {path}")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if mode not in ("add", "replace"): 
            raise HTTPException(status_code=400, detail=f"bad mode for {path}")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        wrote.append(path)

    t.status = "applied"
    db.add(BuilderEvent(kind="apply", msg=f"applied {len(wrote)} files", meta_json=json.dumps(wrote)))
    db.commit()
    return DraftOut(task_id=t.id, files=proposed, diff_summary=f"applied {len(wrote)} files")

@router.post("/telemetry")
def telemetry(payload: TelemetryIn, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    db.add(BuilderEvent(kind=payload.kind, msg=payload.msg or "", meta_json=payload.meta_json or ""))
    db.commit()
    return {"ok": True}
