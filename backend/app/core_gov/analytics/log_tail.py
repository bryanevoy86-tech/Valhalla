"""Log tail helper - reusable utility for reading last N lines of files."""
from __future__ import annotations

from pathlib import Path


def tail_lines(path: Path, max_lines: int = 200) -> list[str]:
    """Read last N lines from a file, safely handling missing files."""
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return lines[-max_lines:]
