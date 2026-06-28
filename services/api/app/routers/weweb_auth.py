"""WeWeb authentication compatibility layer.

This router provides a thin compatibility layer for WeWeb login/session management.
It maps WeWeb-friendly endpoints to the existing /ops/* auth system.

Routes:
  POST /api/weweb/login     - Login with email/password, returns access token
  GET  /api/weweb/me        - Get current user info (requires Bearer token)
  GET  /api/weweb/smoke     - Public health check
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field

from ..security.auth import (
    SETTINGS,
    jwt_decode,
    jwt_encode,
    require_owner,
    verify_owner_password,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/weweb", tags=["weweb"])

# ============================================================================
# Pydantic Models
# ============================================================================


class LoginRequest(BaseModel):
    """WeWeb login request."""
    email: str = Field(..., description="Email or username")
    password: str = Field(..., description="Password")


class LoginResponse(BaseModel):
    """Successful login response."""
    ok: bool = True
    access_token: str = Field(..., description="JWT access token")
    token_type: str = "bearer"
    user: Dict[str, str] = Field(
        ...,
        description="User info",
        example={"email": "owner@valhalla.local", "role": "owner"},
    )


class LoginErrorResponse(BaseModel):
    """Failed login response."""
    ok: bool = False
    detail: str


class MeResponse(BaseModel):
    """Current user info response."""
    ok: bool = True
    user: Dict[str, str] = Field(
        ...,
        description="User info",
        example={"email": "owner@valhalla.local", "role": "owner"},
    )


class SmokeResponse(BaseModel):
    """Health check response."""
    ok: bool = True
    message: str = "WeWeb auth bridge live"


# ============================================================================
# OAuth2 Security
# ============================================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/weweb/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Validate Bearer token and return user payload."""
    if not SETTINGS.enabled:
        raise HTTPException(status_code=503, detail="Auth disabled")

    payload = jwt_decode(token, SETTINGS.jwt_secret)
    if payload.get("sub") != SETTINGS.owner_username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
    return payload


# ============================================================================
# Routes
# ============================================================================


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={401: {"model": LoginErrorResponse, "description": "Invalid credentials"}},
)
def weweb_login(req: LoginRequest) -> LoginResponse:
    """Login with email/password, return access token.
    
    Maps email field to the configured owner username.
    Use the returned access_token in Authorization: Bearer <token> header.
    """
    if not SETTINGS.enabled:
        raise HTTPException(status_code=503, detail="Auth disabled")

    # Treat email as username for compatibility
    username = req.email.strip()
    password = req.password

    # Verify credentials against configured owner
    if username != SETTINGS.owner_username or not verify_owner_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Generate JWT token
    now = int(time.time())
    payload = {
        "sub": SETTINGS.owner_username,
        "iat": now,
        "exp": now + SETTINGS.token_ttl_seconds,
    }
    token = jwt_encode(payload, SETTINGS.jwt_secret)

    return LoginResponse(
        ok=True,
        access_token=token,
        token_type="bearer",
        user={
            "email": SETTINGS.owner_username,
            "role": "owner",
        },
    )


@router.get("/me", response_model=MeResponse)
def weweb_me(payload: Dict[str, Any] = Depends(get_current_user)) -> MeResponse:
    """Get current user info.
    
    Requires Authorization: Bearer <token> header.
    Returns 401 if token is missing or invalid.
    """
    return MeResponse(
        ok=True,
        user={
            "email": SETTINGS.owner_username,
            "role": "owner",
        },
    )


@router.get("/smoke", response_model=SmokeResponse)
def weweb_smoke() -> SmokeResponse:
    """Public health check for WeWeb bridge.
    
    No authentication required.
    Always returns 200 OK if the service is running.
    """
    return SmokeResponse(
        ok=True,
        message="WeWeb auth bridge live",
    )
