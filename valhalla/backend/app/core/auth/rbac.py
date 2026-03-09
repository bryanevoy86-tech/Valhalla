from __future__ import annotations

from typing import Callable, Iterable, Optional
from fastapi import Depends, HTTPException, status

# NOTE:
# Replace this with your real auth user dependency.
# This stub expects request.state.user or returns None.

class UserLike:
    def __init__(self, role: str):
        self.role = role


def get_current_user_stub() -> Optional[UserLike]:
    # TODO: wire your real auth here
    return None


def require_role(allowed: Iterable[str]) -> Callable:
    allowed_set = set(allowed)

    def dep(user: Optional[UserLike] = Depends(get_current_user_stub)) -> UserLike:
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        if user.role not in allowed_set:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return dep
