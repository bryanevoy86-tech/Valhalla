from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

from ops.lead_exporter import export_leads_csv


# Keys that indicate a dict-like "lead"
_SCORE_KEYS = {"score", "lead_score", "readiness_score", "quality_score", "rank_score"}
_ID_KEYS = {"lead_id", "id", "uuid"}


def _is_lead_dict(x: Any) -> bool:
    if not isinstance(x, dict):
        return False
    keys = {str(k).lower() for k in x.keys()}
    has_score = any(k in keys for k in _SCORE_KEYS)
    # id is optional; score is the main requirement
    return has_score


def _score_from_lead(d: Dict[str, Any]) -> float:
    for k in ("score", "lead_score", "readiness_score", "quality_score", "rank_score"):
        if k in d and d[k] is not None:
            try:
                return float(d[k])
            except Exception:
                return 0.0
    return 0.0


def _looks_like_lead_list(v: Any) -> bool:
    if not isinstance(v, list):
        return False
    if len(v) == 0:
        return False
    # Sample a few items
    sample = v[: min(10, len(v))]
    leadish = sum(1 for x in sample if _is_lead_dict(x))
    return leadish >= max(1, len(sample) // 2)


def _choose_best_candidate(candidates: List[Tuple[str, List[Dict[str, Any]]]]) -> Optional[Tuple[str, List[Dict[str, Any]]]]:
    """
    Prefer:
    - larger list
    - higher average score (often indicates post-scoring list)
    """
    if not candidates:
        return None

    scored: List[Tuple[float, int, str, List[Dict[str, Any]]]] = []
    for name, lst in candidates:
        if not lst:
            continue
        avg = sum(_score_from_lead(x) for x in lst) / max(1, len(lst))
        scored.append((avg, len(lst), name, lst))

    if not scored:
        return None

    # Sort by avg score desc, then size desc
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    best = scored[0]
    return (best[2], best[3])


def export_scored_leads_from_locals(
    local_vars: Dict[str, Any],
    out_dir: str = "ops/exports",
    filename_prefix: str = "sandbox_leads",
    limit: int = 5000,
    quiet: bool = False,
) -> Optional[str]:
    """
    Searches locals() for a list of dicts that looks like scored leads,
    exports to CSV, returns the file path string if exported.
    """
    candidates: List[Tuple[str, List[Dict[str, Any]]]] = []

    for name, v in local_vars.items():
        try:
            if _looks_like_lead_list(v):
                # type: ignore
                lead_list = [x for x in v if isinstance(x, dict)]
                candidates.append((name, lead_list))
        except Exception:
            continue

    chosen = _choose_best_candidate(candidates)
    if not chosen:
        if not quiet:
            print("[EXPORT] No scored lead list found in locals(). (This is OK if your loop doesn't keep leads in locals.)")
        return None

    var_name, lead_list = chosen
    path = export_leads_csv(lead_list, out_dir=out_dir, filename_prefix=filename_prefix, limit=limit)

    if not quiet:
        print(f"[EXPORT] Exported leads CSV from '{var_name}' -> {path}")

    return str(path)
