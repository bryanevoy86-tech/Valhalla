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
        from .filtering import filter_board
        b = board()
        subject_id = (rec or {}).get("subject_id") or ""
        b2 = filter_board(b, subject_id=subject_id)
        return {"ok": True, "scope": "jv_board", "subject_id": subject_id, "board": b2}
    except Exception as e:
        return {"ok": False, "error": f"board unavailable: {type(e).__name__}"}

