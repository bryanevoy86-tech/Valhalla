from __future__ import annotations

from typing import Any, Dict, List

def get_dashboard() -> Dict[str, Any]:
    partners_total = 0
    partners_by_type: Dict[str, int] = {}
    deals_open_est = 0
    
    warnings = []
    
    try:
        from backend.app.core_gov.partners import service as psvc  # type: ignore
        partners = psvc.list_partners()
        partners_total = len(partners)
        for p in partners:
            pt = p.get("partner_type", "unknown")
            partners_by_type[pt] = partners_by_type.get(pt, 0) + 1
    except Exception as e:
        warnings.append(f"partners unavailable: {type(e).__name__}: {e}")
    
    try:
        from backend.app.core_gov.deals import service as dsvc  # type: ignore
        deals = dsvc.list_deals()
        deals_open_est = len([d for d in deals if d.get("status") == "open"])
    except Exception as e:
        warnings.append(f"deals unavailable: {type(e).__name__}: {e}")
    
    return {
        "partners_total": partners_total,
        "partners_by_type": partners_by_type,
        "deals_open_est": deals_open_est,
        "warnings": warnings,
    }
