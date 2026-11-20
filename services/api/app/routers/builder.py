import json
import hashlib
import difflib
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

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

MAX_BATCH_FILES = 25
MAX_BATCH_BYTES = 1_000_000


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _read_base(path: str) -> tuple[str, str | None]:
    target = _source_path(path)
    try:
        if not target.exists():
            return "", None
        if not target.is_file() or target.stat().st_size > settings.BUILDER_MAX_FILE_BYTES:
            raise HTTPException(status_code=413, detail="base is not a bounded source file")
        data = target.read_bytes()
        if len(data) > settings.BUILDER_MAX_FILE_BYTES:
            raise HTTPException(status_code=413, detail="base exceeds source size limit")
        return data.decode("utf-8"), _sha(data)
    except HTTPException:
        raise
    except (OSError, UnicodeError):
        raise HTTPException(status_code=409, detail="base source unavailable or not UTF-8") from None


def _locked_task(db: Session, task_id: int) -> BuilderTask:
    task = db.query(BuilderTask).filter(BuilderTask.id == task_id).with_for_update().first()
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    if task.status not in {"queued", "drafted", "review_ready"}:
        raise HTTPException(status_code=409, detail="task state is not editable")
    return task


def _prepare_files(files: list[FileSpec]) -> tuple[list[dict], list[dict]]:
    """Read-only source snapshot; no source mutations or Git operations."""
    if not 1 <= len(files) <= MAX_BATCH_FILES:
        raise HTTPException(status_code=422, detail="invalid Builder batch size")
    records, diffs, seen = [], [], set()
    total = 0
    for spec in files:
        path = spec.path
        target = _source_path(path)
        canonical_path = target.relative_to(_REPO_ROOT.resolve()).as_posix()
        identity = str(target)
        if identity in seen:
            raise HTTPException(status_code=422, detail="duplicate normalized Builder target")
        seen.add(identity)
        content = spec.content.encode("utf-8")
        total += len(content)
        if len(content) > settings.BUILDER_MAX_FILE_BYTES or total > MAX_BATCH_BYTES:
            raise HTTPException(status_code=413, detail="Builder batch exceeds byte limit")
        old, base_sha = _read_base(canonical_path)
        if spec.mode not in {"add", "replace"}:
            raise HTTPException(status_code=422, detail="invalid Builder file mode")
        if spec.mode == "add" and base_sha is not None:
            raise HTTPException(status_code=409, detail="add target already exists")
        if spec.mode == "replace" and base_sha is None:
            raise HTTPException(status_code=409, detail="replace target does not exist")
        if spec.mode == "replace" and old == spec.content:
            raise HTTPException(status_code=422, detail="replacement does not change source")
        records.append({"path": canonical_path, "content": spec.content, "mode": spec.mode,
                        "base_sha256": base_sha, "content_sha256": _sha(content)})
        patch = "".join(difflib.unified_diff(
            old.splitlines(keepends=True), spec.content.splitlines(keepends=True),
            fromfile="/dev/null" if base_sha is None else f"a/{canonical_path}",
            tofile=f"b/{canonical_path}",
        ))
        # The review bundle includes exact content as well as a human-readable
        # diff (difflib output alone is not guaranteed to be git-apply compatible).
        diffs.append({"path": canonical_path, "diff": patch})
    return records, diffs


@router.post("/draft")
def draft(
    files: List[FileSpec],
    task_id: int = Query(..., description="Task ID to attach draft to"),
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    task = _locked_task(db, task_id)
    records, diffs = _prepare_files(files)
    envelope = {"version": 2, "task_id": task.id, "files": records}
    digest = _sha(_canonical(envelope))
    if len(_canonical(envelope)) > 2 * MAX_BATCH_BYTES:
        raise HTTPException(status_code=413, detail="encoded Builder bundle exceeds limit")
    task.payload_json = _canonical({"bundle": envelope, "sha256": digest}).decode("utf-8")
    task.status = "drafted"
    task.diff_summary = f"{len(records)} proposed files; source unchanged"
    db.add(BuilderEvent(kind="draft", msg="snapshot-bound draft stored",
                        meta_json=json.dumps({"task_id": task.id, "sha256": digest,
                                              "file_count": len(records)})))
    db.commit()
    return {"ok": True, "status": "drafted", "changed": len(records), "files": diffs,
            "patch": "".join(d["diff"] for d in diffs), "bundle_sha256": digest,
            "source_modified": False, "tests_verified": False}


def _review_bundle(task: BuilderTask) -> tuple[dict, list[dict]]:
    try:
        stored = json.loads(task.payload_json or "null")
        if not isinstance(stored, dict) or set(stored) != {"bundle", "sha256"}:
            raise ValueError("legacy or malformed draft")
        bundle = stored["bundle"]
        if (not isinstance(bundle, dict) or bundle.get("version") != 2
                or bundle.get("task_id") != task.id
                or _sha(_canonical(bundle)) != stored["sha256"]):
            raise ValueError("bundle identity mismatch")
        specs = [FileSpec.model_validate(row) for row in bundle["files"]]
    except (ValueError, TypeError, KeyError):
        raise HTTPException(status_code=409, detail="Builder draft must be regenerated") from None
    records, diffs = _prepare_files(specs)
    if records != bundle["files"]:
        raise HTTPException(status_code=409, detail="Builder base changed; regenerate draft")
    return stored, diffs


@router.post("/apply", response_model=DraftOut)
def apply(payload: ApplyIn, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    """Retain the historical dry-run contract, never apply code in the API process."""
    if payload.approve:
        raise HTTPException(status_code=409, detail="Direct Builder source writes disabled; use isolated tested PR release")
    task = _locked_task(db, payload.task_id)
    stored, diffs = _review_bundle(task)
    if task.status != "review_ready":
        task.status = "review_ready"
        task.diff_summary = f"{len(diffs)} snapshot-verified proposed files; no tests or deployment"
        db.add(BuilderEvent(kind="review_ready", msg="verified source snapshot and bundle",
                            meta_json=json.dumps({"task_id": task.id, "sha256": stored["sha256"]})))
        db.commit()
    # Preserve the historical synthetic diff file and return the exact work
    # separately via /tasks/{id}/review-bundle.
    patch_file = FileSpec(path="__DIFF__.patch", content="".join(d["diff"] for d in diffs), mode="add")
    return DraftOut(task_id=task.id, files=[patch_file], diff_summary=task.diff_summary or "")


@router.get("/tasks/{task_id}/review-bundle")
def review_bundle(task_id: int, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    task = _locked_task(db, task_id)
    stored, _ = _review_bundle(task)
    if task.status != "review_ready":
        raise HTTPException(status_code=409, detail="prepare review with approve=false first")
    return {**stored, "status": "review_ready", "source_modified": False,
            "tests_verified": False, "deployed": False}


@router.post("/telemetry")
def telemetry(payload: TelemetryIn, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    db.add(BuilderEvent(kind=payload.kind, msg=payload.msg or "", meta_json=payload.meta_json or ""))
    db.commit()
    return {"ok": True}
