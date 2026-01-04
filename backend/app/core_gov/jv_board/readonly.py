from __future__ import annotations
from typing import Any, Dict

def readonly(token: str) -> Dict[str, Any]:
    try:
        from backend.app.core_gov.share_tokens.guard import check  # type: ignore
        ok, msg, rec = check(token=token, scope="jv_board")
        if not ok:
            return {"ok": False, "error": msg}
    except Exception as e:
        return {"ok": False, "error": f"token check failed: {type(e).__name__}"}
    
    try:
        from .service import board
        b = board()
        # optionally filter by subject_id later (partner-specific)
        return {"ok": True, "scope": "jv_board", "board": b}
    except Exception as e:
        return {"ok": False, "error": f"board unavailable: {type(e).__name__}"}
