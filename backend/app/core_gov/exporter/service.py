from __future__ import annotations

import os
import uuid
import zipfile
from datetime import datetime, timezone
from typing import Dict, List, Tuple

DATA_ROOT = os.path.join("backend", "data")
EXPORT_DIR = os.path.join(DATA_ROOT, "exports")
INDEX_PATH = os.path.join(EXPORT_DIR, "backups.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    if not os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            f.write('{"updated_at":"%s","items":[]}' % _utcnow_iso())


def _read_index() -> Dict:
    _ensure()
    import json
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_index(items: List[Dict]) -> None:
    _ensure()
    import json
    tmp = INDEX_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "items": items}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, INDEX_PATH)


def _walk_json_files() -> List[str]:
    files = []
    for root, dirs, filenames in os.walk(DATA_ROOT):
        # skip exports folder inside data to avoid recursive inclusion
        if os.path.abspath(root).startswith(os.path.abspath(EXPORT_DIR)):
            continue
        for fn in filenames:
            if fn.lower().endswith(".json"):
                files.append(os.path.join(root, fn))
    files.sort()
    return files


def create_backup() -> Dict:
    _ensure()
    backup_id = "bkp_" + uuid.uuid4().hex[:12]
    ts = datetime.now(timezone.utc)
    fname = f"{backup_id}__{ts.strftime('%Y%m%dT%H%M%SZ')}.zip"
    out_path = os.path.join(EXPORT_DIR, fname)

    files = _walk_json_files()
    included = []
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in files:
            rel = os.path.relpath(path, start=DATA_ROOT)
            z.write(path, arcname=rel)
            included.append(rel)

    size = os.path.getsize(out_path)

    rec = {
        "ok": True,
        "backup_id": backup_id,
        "created_at": ts.isoformat(),
        "file_path": out_path,
        "file_name": fname,
        "bytes": int(size),
        "included_files": included,
    }

    idx = _read_index()
    items = idx.get("items", [])
    items.append(rec)
    items = items[-200:]  # cap
    _write_index(items)
    return rec


def list_backups(limit: int = 25) -> List[Dict]:
    idx = _read_index()
    items = list(reversed(idx.get("items", [])))
    return items[: max(1, min(limit, 200))]


def get_backup(backup_id: str) -> Dict | None:
    idx = _read_index()
    for rec in idx.get("items", []):
        if rec.get("backup_id") == backup_id:
            return rec
    return None
