import json, os
import hashlib
import tempfile
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from slugify import slugify

from ..core.db import get_db
from ..core.settings import settings
from ..core.dependencies import require_builder_key
from ..core.builder_path_policy import resolve_builder_path, BuilderPathRejected
from ..models.builder import BuilderTask, BuilderEvent
from ..schemas.builder import (
    RegisterIn, RegisterOut, TaskIn, TaskOut, DraftOut, FileSpec, TelemetryIn, ApplyIn
)

router = APIRouter(prefix="/builder", tags=["builder"])

_REPO_ROOT = Path(__file__).resolve().parents[4]


def _source_path(path: str) -> Path:
    """Always resolve against repository root, never the Render working dir."""
    try:
        return resolve_builder_path(path, settings.BUILDER_ALLOWED_DIRS, _REPO_ROOT)
    except BuilderPathRejected as exc:
        raise HTTPException(status_code=400, detail=f"builder path denied: {exc}") from None


def _path_is_allowed(path: str) -> bool:
    try:
        _source_path(path)
        return True
    except HTTPException:
        return False

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

def _read_text(path: str) -> str:
    try:
        with _source_path(path).open("r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return ""

def _unified_diff(old: str, new: str, path: str) -> str:
    import difflib
    a = old.splitlines(keepends=True)
    b = new.splitlines(keepends=True)
    return "".join(difflib.unified_diff(a, b, fromfile=f"a/{path}", tofile=f"b/{path}"))

@router.post("/draft")
def draft(
    files: List[FileSpec],
    task_id: int = Query(..., description="Task ID to attach draft to"),
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    # Validate task
    t = db.get(BuilderTask, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="task not found")
    # Dry-run: compute diffs without writing and persist proposed files on the task
    diffs = []
    combined_patch_parts: List[str] = []
    changed = 0
    for f in files:
        path = f.path.strip()
        if not _path_is_allowed(path):
            raise HTTPException(status_code=400, detail=f"path not allowed: {path}")
        if len(f.content.encode("utf-8")) > settings.BUILDER_MAX_FILE_BYTES:
            raise HTTPException(status_code=413, detail=f"file too large: {path}")
        old = _read_text(path)
        patch = _unified_diff(old, f.content, path)
        diffs.append({"path": path, "diff": patch})
        if patch:
            changed += 1
            combined_patch_parts.append(patch)
    # Persist proposed files to the task
    t.payload_json = json.dumps([f.__dict__ for f in files])
    t.diff_summary = f"{changed} files changed"
    db.add(t); db.commit()
    return {"ok": True, "changed": changed, "files": diffs, "patch": "".join(combined_patch_parts)}

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
        # dry-run diffs using the attached proposed files
        diffs = []
        combined_patch_parts: List[str] = []
        for f in proposed:
            path = f["path"].strip()
            if not _path_is_allowed(path):
                raise HTTPException(status_code=400, detail=f"path not allowed: {path}")
            old = _read_text(path)
            patch = _unified_diff(old, f["content"], path)
            diffs.append({"path": path, "diff": patch})
            if patch:
                combined_patch_parts.append(patch)
        t.diff_summary = f"{sum(1 for d in diffs if d['diff'])} files changed"
        db.add(t); db.commit()
        # Return a synthetic patch file in the DraftOut for convenience
        patch_file = FileSpec(path="__DIFF__.patch", content="".join(combined_patch_parts), mode="add")
        return DraftOut(task_id=t.id, files=[patch_file], diff_summary=t.diff_summary or "")

    # Never push generated code directly from an API request. Changes must
    # be committed via a reviewed GitHub branch/PR with CI evidence.
    if settings.GIT_ENABLE_AUTOCOMMIT:
        raise HTTPException(
            status_code=409,
            detail="Direct Builder git push disabled; use reviewed PR workflow",
        )

    # Preflight the ENTIRE batch before writing any file.
    staged = []
    for item in proposed:
        path = item["path"]
        content = item["content"]
        mode = item.get("mode", "add")
        target = _source_path(path)
        if mode not in ("add", "replace"):
            raise HTTPException(status_code=400, detail=f"bad mode for {path}")
        if len(content.encode("utf-8")) > settings.BUILDER_MAX_FILE_BYTES:
            raise HTTPException(status_code=413, detail=f"file too large: {path}")
        if mode == "add" and target.exists():
            raise HTTPException(status_code=409, detail=f"file already exists: {path}")
        if mode == "replace" and not target.is_file():
            raise HTTPException(status_code=409, detail=f"file missing for replace: {path}")
        staged.append((path, content, target))

    wrote = []
    evidence = []
    for path, content, target in staged:
        # Atomic replacement avoids torn files if a worker crashes during write.
        # No external Git operation is performed by this endpoint.
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".builder-", dir=str(target.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != hashlib.sha256(content.encode("utf-8")).hexdigest():
            raise HTTPException(status_code=500, detail=f"write verification failed: {path}")
        wrote.append(path)
        evidence.append({"path": path, "sha256": digest})


    t.status = "applied"
    db.add(BuilderEvent(kind="apply", msg=f"applied {len(wrote)} files", meta_json=json.dumps(wrote)))
    db.commit()

    db.add(BuilderEvent(kind="write_receipt", msg="verified local-only file writes", meta_json=json.dumps(evidence)))
    db.commit()
    return DraftOut(task_id=t.id, files=proposed, diff_summary=f"applied {len(wrote)} files")

@router.post("/telemetry")
def telemetry(payload: TelemetryIn, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    db.add(BuilderEvent(kind=payload.kind, msg=payload.msg or "", meta_json=payload.meta_json or ""))
    db.commit()
    return {"ok": True}
