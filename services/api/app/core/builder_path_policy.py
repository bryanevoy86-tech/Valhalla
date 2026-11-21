"""Builder filesystem boundary.

Validate a proposed relative source path against explicitly allowed directories.
Never treat string prefix checks as a filesystem security boundary.
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath


class BuilderPathRejected(ValueError):
    """Proposed write escapes the owner-authorized source locations."""


def resolve_builder_path(
    raw_path: str,
    allowed_dirs: list[str],
    repo_root: str | Path,
) -> Path:
    if not isinstance(raw_path, str) or not raw_path or raw_path != raw_path.strip():
        raise BuilderPathRejected("path must be a nonblank, unambiguous relative path")

    normalized = raw_path.replace("\\", "/")
    path = PurePosixPath(normalized)
    parts = path.parts

    if (
        normalized.startswith(("/", "~"))
        or ":" in normalized
        or "\x00" in normalized
        or path.is_absolute()
        or len(parts) < 2
        or any(part in (".", "..", "") for part in normalized.split("/"))
        or any(ord(c) < 32 for c in normalized)
    ):
        raise BuilderPathRejected("absolute, traversal, or ambiguous path refused")

    root = Path(repo_root).resolve(strict=True)
    target = root.joinpath(*parts).resolve(strict=False)

    if not target.is_relative_to(root) or target == root:
        raise BuilderPathRejected("target leaves repository")

    # A root-owned allowlist cannot be expanded by a user-supplied target.
    for raw_allowed in allowed_dirs:
        allowed = PurePosixPath(raw_allowed.replace("\\", "/"))
        if allowed.is_absolute() or ".." in allowed.parts or ":" in str(allowed):
            continue
        allowed_path = root.joinpath(*allowed.parts).resolve(strict=False)
        if not allowed_path.is_relative_to(root):
            continue
        if target.is_relative_to(allowed_path) and target != allowed_path:
            return target

    raise BuilderPathRejected("target outside allowed source directories")
