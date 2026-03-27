from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from .identity import get_identity
from .models import Identity

def require_active_subscription(request: Request) -> Identity:
    ident = get_identity(request)
    if not ident.is_active_subscription:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Subscription inactive")
    return ident

def require_scopes(*required: str):
    def dep(request: Request) -> Identity:
        ident = get_identity(request)
        missing = [r for r in required if r not in ident.scopes]
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing scopes: {missing}")
        return ident
    return Depends(dep)
