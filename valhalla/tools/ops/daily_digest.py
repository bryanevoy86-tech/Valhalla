from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List


def _count_files(path: Path, pattern: str = "*") -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.rglob(pattern) if _.is_file())


def _recent_files(path: Path, n: int = 25) -> List[str]:
    if not path.exists():
        return []
    files = [p for p in path.rglob("*") if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [str(p) for p in files[:n]]


def _find_export_dirs() -> Dict[str, str]:
    # Heuristic: common locations used in this repo style.
    candidates = [
        Path("data/exports/phase3"),
        Path("exports"),
        Path("data/exports"),
        Path("reports"),
        Path("reports/integrated_sandbox"),
    ]
    found = {}
    for c in candidates:
        if c.exists():
            found[c.name] = str(c)
    return found


def build_digest() -> Dict[str, Any]:
    tz = os.getenv("TZ", "local")
    now_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    today = time.strftime("%Y-%m-%d", time.localtime())

    export_dirs = _find_export_dirs()
    inbox = Path(os.getenv("VALHALLA_REAL_LEADS_DIR", "data/inbox/real_leads"))
    quarantine = Path("data/inbox/quarantine")
    integrated_reports = Path("reports/integrated_sandbox")
    digest_out = Path("reports/daily_digest")

    payload: Dict[str, Any] = {
        "timestamp_utc": now_utc,
        "local_date": today,
        "timezone_hint": tz,
        "env": {
            "VALHALLA_PHASE": os.getenv("VALHALLA_PHASE"),
            "VALHALLA_REAL_DATA_INGEST": os.getenv("VALHALLA_REAL_DATA_INGEST"),
            "VALHALLA_DRY_RUN": os.getenv("VALHALLA_DRY_RUN"),
            "VALHALLA_DISABLE_OUTBOUND": os.getenv("VALHALLA_DISABLE_OUTBOUND"),
        },
        "paths": {
            "inbox": str(inbox),
            "quarantine": str(quarantine),
            "integrated_reports": str(integrated_reports),
            "export_dirs_detected": export_dirs,
            "digest_dir": str(digest_out),
        },
        "counts": {
            "inbox_files": _count_files(inbox),
            "quarantine_files": _count_files(quarantine),
            "integrated_reports": _count_files(integrated_reports),
        },
        "recent": {
            "inbox": _recent_files(inbox, 10),
            "quarantine": _recent_files(quarantine, 10),
            "integrated_reports": _recent_files(integrated_reports, 10),
        },
        "notes": [
            "Digest is read-only; it does not modify sandbox state.",
            "If export dirs are missing, add your actual export path to candidates in this script."
        ]
    }

    # Add counts for each detected export directory
    for label, path_str in export_dirs.items():
        p = Path(path_str)
        payload["counts"][f"files_in_{label}"] = _count_files(p)

    return payload


def write_digest(payload: Dict[str, Any]) -> None:
    out_dir = Path("reports/daily_digest")
    out_dir.mkdir(parents=True, exist_ok=True)

    today = payload.get("local_date", "unknown-date")
    daily_path = out_dir / f"{today}.json"
    latest_path = out_dir / "latest.json"

    daily_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    latest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote: {daily_path}")
    print(f"Wrote: {latest_path}")


if __name__ == "__main__":
    write_digest(build_digest())
