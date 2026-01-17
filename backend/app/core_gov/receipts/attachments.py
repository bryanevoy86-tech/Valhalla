from __future__ import annotations
import hashlib, os
from typing import Any, Dict

def file_fingerprint(file_path: str) -> Dict[str, Any]:
    p = (file_path or "").strip()
    if not p:
        raise ValueError("file_path required")
    if not os.path.exists(p):
        raise FileNotFoundError("file not found")

    h = hashlib.sha256()
    size = 0
    with open(p, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            h.update(chunk)
    return {"file_path": p, "bytes": size, "sha256": h.hexdigest()}
