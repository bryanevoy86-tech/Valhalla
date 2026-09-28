import json
import os
from datetime import datetime, timezone
from pathlib import Path


def _buildinfo_path() -> Path:
    explicit = os.getenv("BUILDINFO_PATH")
    if explicit:
        return Path(explicit)
    return Path(__file__).resolve().parents[1] / "buildinfo.json"


def _read_buildinfo() -> dict:
    path = _buildinfo_path()
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
            if isinstance(payload, dict):
                return payload
    except Exception:
        pass
    return {}


def _normalize_sha(value: str | None) -> str:
    if not value:
        return "UNKNOWN"
    value = value.strip()
    if not value:
        return "UNKNOWN"
    return value


def _short_sha(value: str) -> str:
    if value in {"", "UNKNOWN"}:
        return "UNKNOWN"
    return value[:7]


def get_runtime_build_identity() -> dict:
    """Return deployment/build identity fields with explicit source provenance."""
    payload = _read_buildinfo()

    file_sha = _normalize_sha(str(payload.get("git_sha", "UNKNOWN")))
    file_built_at = str(payload.get("built_at", "UNKNOWN"))
    file_version = str(payload.get("version", "0.0.0"))

    env_sha = (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("GIT_SHA")
        or os.getenv("COMMIT_SHA")
        or os.getenv("SOURCE_COMMIT")
    )
    git_sha = _normalize_sha(env_sha) if env_sha else file_sha
    git_sha_source = "env" if env_sha else "buildinfo"

    observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "git_sha": git_sha,
        "git_sha_short": _short_sha(git_sha),
        "git_sha_source": git_sha_source,
        "built_at": file_built_at,
        "version": file_version,
        "buildinfo_path": str(_buildinfo_path()),
        "observed_at": observed_at,
    }
