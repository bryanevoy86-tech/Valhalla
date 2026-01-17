from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

DATA_DIR = os.path.join("backend", "data", "know")
DOCS_PATH = os.path.join(DATA_DIR, "docs.json")
CHUNKS_PATH = os.path.join(DATA_DIR, "chunks.json")
INDEX_PATH = os.path.join(DATA_DIR, "index.json")

# Inbox is simple file drop (text) for later automation.
INBOX_DIR = os.path.join(DATA_DIR, "inbox")
CLEAN_DIR = os.path.join(DATA_DIR, "clean")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(INBOX_DIR, exist_ok=True)
    os.makedirs(CLEAN_DIR, exist_ok=True)
    if not os.path.exists(DOCS_PATH):
        with open(DOCS_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)
    if not os.path.exists(CHUNKS_PATH):
        with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)
    if not os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "terms": {}, "chunk_meta": {}}, f, indent=2)


def _read(path: str) -> Dict[str, Any]:
    _ensure()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write(path: str, data: Dict[str, Any]) -> None:
    _ensure()
    data["updated_at"] = _utcnow_iso()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


# ---- Docs ----
def list_docs() -> List[Dict[str, Any]]:
    data = _read(DOCS_PATH)
    return data.get("items", [])


def save_docs(items: List[Dict[str, Any]]) -> None:
    _write(DOCS_PATH, {"items": items})


# ---- Chunks ----
def list_chunks() -> List[Dict[str, Any]]:
    data = _read(CHUNKS_PATH)
    return data.get("items", [])


def save_chunks(items: List[Dict[str, Any]]) -> None:
    _write(CHUNKS_PATH, {"items": items})


# ---- Index ----
def read_index() -> Dict[str, Any]:
    return _read(INDEX_PATH)


def write_index(index: Dict[str, Any]) -> None:
    _write(INDEX_PATH, index)


# ---- Inbox helpers ----
def list_inbox_files() -> List[str]:
    _ensure()
    files = []
    for name in os.listdir(INBOX_DIR):
        p = os.path.join(INBOX_DIR, name)
        if os.path.isfile(p):
            files.append(name)
    files.sort()
    return files


def read_inbox_file(name: str) -> str:
    _ensure()
    p = os.path.join(INBOX_DIR, name)
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def move_inbox_to_clean(name: str, clean_text: str) -> str:
    _ensure()
    src = os.path.join(INBOX_DIR, name)
    dst = os.path.join(CLEAN_DIR, name)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(clean_text)
    if os.path.exists(src):
        os.remove(src)
    return dst
