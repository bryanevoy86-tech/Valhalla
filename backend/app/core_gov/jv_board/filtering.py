from __future__ import annotations
from typing import Any, Dict

def filter_board(board: Dict[str, Any], subject_id: str) -> Dict[str, Any]:
    """
    v1: if subject_id is present, filter deals/rows that match partner_id==subject_id (where available).
    Non-matching rows are removed.
    """
    if not subject_id:
        return board

    out = dict(board)
    # common fields we may have:
    for key in ("deals", "items", "rows"):
        if key in out and isinstance(out[key], list):
            out[key] = [x for x in out[key] if (x.get("partner_id") or (x.get("meta") or {}).get("partner_id")) == subject_id]
    out["filtered_for_partner"] = subject_id
    return out
