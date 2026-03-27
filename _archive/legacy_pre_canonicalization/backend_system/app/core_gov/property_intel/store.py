from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "property_intel")
PROPS_PATH = os.path.join(DATA_DIR, "properties.json")
COMPS_PATH = os.path.join(DATA_DIR, "comps.json")
REPAIRS_PATH = os.path.join(DATA_DIR, "repairs.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    for path in [PROPS_PATH, COMPS_PATH, REPAIRS_PATH]:
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)


def list_properties() -> List[Dict[str, Any]]:
    _ensure()
    with open(PROPS_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])


def save_properties(items: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = PROPS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "items": items}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PROPS_PATH)


def list_comps() -> List[Dict[str, Any]]:
    _ensure()
    with open(COMPS_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])


def save_comps(items: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = COMPS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "items": items}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, COMPS_PATH)


def list_repairs() -> List[Dict[str, Any]]:
    _ensure()
    with open(REPAIRS_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])


def save_repairs(items: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = REPAIRS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "items": items}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, REPAIRS_PATH)
