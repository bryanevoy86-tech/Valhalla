from __future__ import annotations

from pathlib import Path
import zipfile
import datetime as dt

DATA_DIR = Path("data")
EXPORT_DIR = DATA_DIR / "exports"

DEFAULT_FILES = [
    "cone_state.json",
    "thresholds.json",
    "capital_usage.json",
    "alerts.json",
    "go_progress.json",
    "go_session.json",
    "leads.json",
    "weekly_audits.json",
    "audit_log.json",
]


def _now_tag() -> str:
    return dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def build_export_bundle(files: list[str] | None = None) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    tag = _now_tag()
    out_path = EXPORT_DIR / f"valhalla_export_{tag}.zip"

    use_files = files or DEFAULT_FILES

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for fname in use_files:
            fpath = DATA_DIR / fname
            if fpath.exists() and fpath.is_file():
                z.write(fpath, arcname=fname)

    return out_path
