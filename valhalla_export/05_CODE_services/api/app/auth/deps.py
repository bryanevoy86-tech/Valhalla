"""Auth dependency functions for FastAPI routers."""

from fastapi import Depends, HTTPException, status


def get_current_user():
    """Placeholder user retrieval. Replace with real auth later."""
    return {"id": "system", "role": "admin"}


def require_admin(user=Depends(get_current_user)):
    """Placeholder admin check."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    return user
