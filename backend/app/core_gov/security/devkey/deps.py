from __future__ import annotations

from fastapi import HTTPException, Request, status

from ...settings.config import load_settings

def require_dev_key(request: Request) -> None:
    """Check X-VALHALLA-KEY header if dev key is configured."""
    s = load_settings()
    if not s.VALHALLA_DEV_KEY:
        # If no key configured, do nothing (dev mode).
        return

    provided = request.headers.get("X-VALHALLA-KEY")
    if not provided or provided != s.VALHALLA_DEV_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing/invalid X-VALHALLA-KEY",
        )

