from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def export_leads_csv(
    leads: Iterable[Dict[str, Any]],
    out_dir: str = "ops/exports",
    filename_prefix: str = "sandbox_leads",
    limit: int = 5000,
) -> Path:
    """
    Write a CSV snapshot of lead objects.

    Expected keys (best effort):
      - lead_id / id / uuid
      - score / lead_score / readiness_score
      - source / lead_source

    Pure export. Does NOT modify leads or sandbox DB.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    for i, lead in enumerate(leads):
        if i >= limit:
            break
        rows.append(lead or {})

    def pick(row: Dict[str, Any], keys: List[str], default: Any = "") -> Any:
        for k in keys:
            if k in row and row[k] is not None:
                return row[k]
        return default

    normalized = []
    for r in rows:
        normalized.append(
            {
                "lead_id": str(pick(r, ["lead_id", "id", "uuid"], "")),
                "score": pick(
                    r,
                    ["score", "lead_score", "readiness_score", "quality_score", "rank_score"],
                    0,
                ),
                "source": str(pick(r, ["source", "lead_source"], "")),
            }
        )

    stamp = _utc_stamp()
    file_path = out_path / f"{filename_prefix}_{stamp}.csv"

    with file_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["lead_id", "score", "source"])
        w.writeheader()
        for r in normalized:
            w.writerow(r)

    return file_path
