from __future__ import annotations

import csv
import io
from collections.abc import Iterable
from typing import Any, Dict, List


def to_csv(rows: Iterable[Dict[str, Any]], headers: List[str]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=headers, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    return buf.getvalue()


def from_csv(text: str) -> list[dict]:
    buf = io.StringIO(text)
    r = csv.DictReader(buf)
    return [dict(row) for row in r]
