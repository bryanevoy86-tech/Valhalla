"""
WeWeb authentication endpoints for email-based login.

Endpoints:
- POST /api/weweb/login - Login with email + password
- GET /api/weweb/me - Get current user (requires token)
- GET /api/weweb/smoke - Health check (no auth required)
"""

import time
import hmac
import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.users.models import UserProfile, AccountSettings
from app.security.auth import jwt_encode, jwt_decode, pbkdf2_verify

router = APIRouter(prefix="/api/weweb", tags=["weweb-auth"])


# ============================================================================
# Schemas
# ============================================================================

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    ok: bool
    access_token: str
    token_type: str
    user: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    ok: bool
    user: Optional[Dict[str, Any]] = None


# ============================================================================
# OAuth2 Bearer token
# ============================================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/weweb/login", auto_error=False)


def _normalize_email(value: Optional[str]) -> str:
    """Normalize email for stable security comparisons."""
    return (value or "").strip().lower()


def _is_configured_owner(authenticated_email: Optional[str]) -> bool:
    """Resolve owner status from trusted server-side configuration only."""
    configured_owner = _normalize_email(os.getenv("VALHALLA_OWNER_EMAIL"))
    candidate = _normalize_email(authenticated_email)
    if not configured_owner or not candidate:
        return False
    return hmac.compare_digest(candidate, configured_owner)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Extract user from JWT token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Use auth settings to get JWT secret
    from app.security.auth import SETTINGS
    
    payload = jwt_decode(token, SETTINGS.jwt_secret)
    user_id = payload.get("user_id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    return payload


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/login", response_model=LoginResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """
    Login with email and password.
    
    Returns JWT token on success.
    """
    email = credentials.email.strip().lower()
    password = credentials.password
    
    # Find user by email
    user = db.query(UserProfile).filter(
        UserProfile.email == email
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Check if user has account settings (password hash)
    account_settings = db.query(AccountSettings).filter(
        AccountSettings.user_id == user.user_id
    ).first()
    
    if not account_settings:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User has no password set",
        )
    
    # Verify password against hash
    if not pbkdf2_verify(password, account_settings.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Issue JWT token
    from app.security.auth import SETTINGS
    
    now = int(time.time())
    payload = {
        "sub": user.email,
        "user_id": user.user_id,
        "iat": now,
        "exp": now + SETTINGS.token_ttl_seconds,
    }
    token = jwt_encode(payload, SETTINGS.jwt_secret)
    
    return LoginResponse(
        ok=True,
        access_token=token,
        token_type="bearer",
        user={
            "id": user.user_id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
    )


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Get current authenticated user."""
    user_id = current_user.get("user_id")
    
    user = db.query(UserProfile).filter(
        UserProfile.user_id == user_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    is_owner = _is_configured_owner(user.email)
    
    return UserResponse(
        ok=True,
        user={
            "id": user.user_id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_owner": is_owner,
        },
    )


@router.get("/smoke")
def smoke_test() -> Dict[str, Any]:
    """
    Public health check endpoint.
    Confirms WeWeb auth router is active and routes available.
    """
    return {
        "ok": True,
        "status": "operational",
        "router": "auth_weweb",
        "login_path": "/api/weweb/login",
        "me_path": "/api/weweb/me",
        "reset_path": "/api/weweb/admin/reset-owner-password",
    }


@router.post("/admin/reset-owner-password")
def admin_reset_password(
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    BACKUP reset endpoint - only enabled if RESET_OWNER_PASSWORD=true.
    
    Security: 
    - Reads VALHALLA_OWNER_EMAIL from env
    - Reads VALHALLA_OWNER_PASSWORD from env  
    - Requires X-Setup-Token header matching VALHALLA_SETUP_TOKEN (if set)
    - Never returns password or hash
    
    This is a fallback if pre-deploy command fails.
    """
    import os
    
    # Check if reset is enabled
    reset_enabled = (os.getenv("RESET_OWNER_PASSWORD") or "").strip().lower()
    if reset_enabled not in {"true", "1", "yes", "on"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner reset not enabled",
        )
    
    # If setup token is configured, require it
    setup_token = os.getenv("VALHALLA_SETUP_TOKEN")
    if setup_token:
        provided_token = request.headers.get("X-Setup-Token", "")
        if not hmac.compare_digest(provided_token or "", setup_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid setup token",
            )
    
    # Read credentials from env
    email = (os.getenv("VALHALLA_OWNER_EMAIL") or "").strip()
    password = os.getenv("VALHALLA_OWNER_PASSWORD")
    
    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="VALHALLA_OWNER_EMAIL and VALHALLA_OWNER_PASSWORD must be set",
        )
    
    try:
        from app.security.auth import pbkdf2_hash_password
        
        # Get or create user
        user = db.query(UserProfile).filter(
            UserProfile.email == email
        ).first()
        
        if not user:
            user = UserProfile(
                first_name="Admin",
                last_name="Owner",
                email=email,
            )
            db.add(user)
            db.flush()
        
        # Hash password
        password_hash = pbkdf2_hash_password(password)
        
        # Update or create account settings
        account_settings = db.query(AccountSettings).filter(
            AccountSettings.user_id == user.user_id
        ).first()
        
        if account_settings:
            account_settings.password_hash = password_hash
        else:
            account_settings = AccountSettings(
                user_id=user.user_id,
                password_hash=password_hash,
            )
            db.add(account_settings)
        
        db.commit()
        
        return {
            "ok": True,
            "message": f"Owner password reset complete for {email}",
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password",
        ) from e
