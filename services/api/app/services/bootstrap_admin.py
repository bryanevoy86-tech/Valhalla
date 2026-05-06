"""
Bootstrap admin user creation on startup.

One-time flow:
1. Read BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD from env
2. Check if user exists by email
3. If not, create user with securely hashed password
4. Log bootstrap result (created / already exists / skipped)

This is dev-safe and production-aware:
- No credentials in source code
- Passwords not exposed in logs
- Idempotent (safe to run multiple times)
- Gracefully handles missing env vars
- Lazy-loads password hashing to avoid blocking startup
"""

import os
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.users.models import UserProfile, AccountSettings
from app.users.service import UserProfileService

log = logging.getLogger(__name__)


def _get_password_hasher():
    """Lazy-load password hasher to avoid blocking startup on auth import."""
    try:
        from app.security.auth import pbkdf2_hash_password
        return pbkdf2_hash_password
    except Exception as e:
        log.error(f"Could not load password hasher: {e}")
        raise


def _read_bootstrap_env() -> Optional[Dict[str, str]]:
    """
    Read bootstrap credentials from environment.
    Returns {"email": "...", "password": "..."} or None if not configured.
    """
    email = (os.getenv("BOOTSTRAP_ADMIN_EMAIL") or "").strip()
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")

    if not email or not password:
        return None

    return {"email": email, "password": password}


def _user_exists(db: Session, email: str) -> bool:
    """Check if user exists by email."""
    user = db.query(UserProfile).filter(UserProfile.email == email).first()
    return user is not None


def _create_bootstrap_user(db: Session, email: str, password: str) -> UserProfile:
    """
    Create bootstrap admin user with hashed password.
    
    Returns:
        UserProfile: The created user
        
    Raises:
        ValueError: If user already exists or creation fails
    """
    # Check if already exists (defensive against race conditions)
    if _user_exists(db, email):
        raise ValueError(f"User {email} already exists")

    # Create user profile with generic name (bootstrap user)
    profile = UserProfile(
        first_name="Bootstrap",
        last_name="Admin",
        email=email,
    )
    db.add(profile)
    db.flush()  # Get the user_id without committing

    # Lazy-load and hash password using PBKDF2-SHA256
    pbkdf2_hash_password = _get_password_hasher()
    password_hash = pbkdf2_hash_password(password)

    # Create account settings with hashed password
    account_settings = AccountSettings(
        user_id=profile.user_id,
        password_hash=password_hash,
    )
    db.add(account_settings)
    db.commit()
    db.refresh(profile)

    return profile


def bootstrap_admin_user(db: Session) -> Dict[str, Any]:
    """
    Bootstrap admin user creation.
    
    Returns:
        Dict with keys:
        - "ok": bool (True if all is well)
        - "status": str (one of "created", "already_exists", "skipped")
        - "email": str or None (the email, if relevant)
        - "detail": str (human-readable message)
    """
    # Read env vars
    bootstrap_creds = _read_bootstrap_env()

    if not bootstrap_creds:
        return {
            "ok": True,
            "status": "skipped",
            "email": None,
            "detail": "Bootstrap admin disabled (set BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD to enable)",
        }

    email = bootstrap_creds["email"]
    password = bootstrap_creds["password"]

    try:
        # Check if already exists
        if _user_exists(db, email):
            log.info(
                f"Bootstrap admin user '{email}' already exists, skipping creation"
            )
            return {
                "ok": True,
                "status": "already_exists",
                "email": email,
                "detail": f"User {email} already exists",
            }

        # Create user
        user = _create_bootstrap_user(db, email, password)
        log.info(
            f"Bootstrap admin user created successfully: {email} (user_id={user.user_id})"
        )
        return {
            "ok": True,
            "status": "created",
            "email": email,
            "detail": f"Bootstrap admin user {email} created successfully",
        }

    except Exception as e:
        log.error(f"Bootstrap admin creation failed: {e}")
        # Don't expose error details in return value for security
        return {
            "ok": False,
            "status": "error",
            "email": email,
            "detail": "Bootstrap admin creation failed (see logs for details)",
        }
