#!/usr/bin/env python
"""
Safe admin password reset script for Valhalla API.

USAGE:
    # Set environment variables
    export VALHALLA_OWNER_EMAIL="admin@example.com"
    export VALHALLA_OWNER_PASSWORD="MySecurePassword123"
    export RESET_OWNER_PASSWORD="true"
    
    # Run script
    python scripts/reset_owner_password.py

BEHAVIOR:
- Reads VALHALLA_OWNER_EMAIL and VALHALLA_OWNER_PASSWORD from environment
- Connects to DATABASE_URL
- Creates or updates admin user with hashed password
- Never prints password or hash (only email and completion status)
- Exits with code 1 on error

SAFETY NOTES:
- Plain password is only in memory during hashing
- Database stores only PBKDF2-SHA256 hash
- Script is optional - only runs if RESET_OWNER_PASSWORD env var is "true"
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)


def _load_db():
    """Lazy-load SQLAlchemy to avoid startup dependency."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    return create_engine, sessionmaker


def _read_env() -> dict:
    """
    Read required environment variables.
    
    Returns:
        dict with keys: email, password, database_url
        
    Raises:
        RuntimeError: If required vars are missing
    """
    email = (os.getenv("VALHALLA_OWNER_EMAIL") or "").strip()
    password = os.getenv("VALHALLA_OWNER_PASSWORD")
    database_url = os.getenv("DATABASE_URL")
    
    if not email:
        raise RuntimeError("VALHALLA_OWNER_EMAIL is required but not set")
    
    if not password:
        raise RuntimeError("VALHALLA_OWNER_PASSWORD is required but not set")
    
    if not database_url:
        raise RuntimeError("DATABASE_URL is required but not set")
    
    return {
        "email": email,
        "password": password,
        "database_url": database_url,
    }


def _get_password_hasher():
    """Get PBKDF2-SHA256 password hasher from app.security.auth."""
    try:
        # Add app to path
        app_root = Path(__file__).resolve().parent.parent / "services" / "api"
        if app_root.exists():
            sys.path.insert(0, str(app_root.parent))
        
        from app.security.auth import pbkdf2_hash_password
        return pbkdf2_hash_password
    except ImportError as e:
        raise RuntimeError(f"Could not import pbkdf2_hash_password: {e}")


def _ensure_models_loaded():
    """Import models to register them with SQLAlchemy."""
    try:
        from app.users.models import UserProfile, AccountSettings
        from app.core.db import Base
        return UserProfile, AccountSettings, Base
    except ImportError as e:
        raise RuntimeError(f"Could not import models: {e}")


def _get_or_create_admin_user(db_session, email: str):
    """Get existing admin user or create new one."""
    from app.users.models import UserProfile
    
    # Look for existing user by email
    user = db_session.query(UserProfile).filter(
        UserProfile.email.ilike(email)
    ).first()
    
    if user:
        log.info(f"Found existing user for {email}")
        return user
    
    # Create new admin user
    log.info(f"Creating new admin user for {email}")
    user = UserProfile(
        first_name="Admin",
        last_name="Owner",
        email=email,
    )
    db_session.add(user)
    db_session.flush()  # Get user_id without committing
    
    return user


def _reset_admin_password(email: str, password: str) -> bool:
    """
    Reset admin password.
    
    Args:
        email: Admin email
        password: Plain text password (will be hashed)
        
    Returns:
        bool: True on success
        
    Raises:
        Exception: On database or hashing errors
    """
    env_vars = _read_env()
    create_engine, sessionmaker = _load_db()
    UserProfile, AccountSettings, Base = _ensure_models_loaded()
    pbkdf2_hash_password = _get_password_hasher()
    
    # Create database connection
    engine = create_engine(env_vars["database_url"])
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Get or create admin user
        user = _get_or_create_admin_user(db, email)
        
        # Hash password using PBKDF2-SHA256
        log.info("Hashing password...")
        password_hash = pbkdf2_hash_password(password)
        
        # Find or create account settings
        account_settings = db.query(AccountSettings).filter(
            AccountSettings.user_id == user.user_id
        ).first()
        
        if account_settings:
            log.info("Updating existing account settings")
            account_settings.password_hash = password_hash
        else:
            log.info("Creating new account settings")
            account_settings = AccountSettings(
                user_id=user.user_id,
                password_hash=password_hash,
            )
            db.add(account_settings)
        
        # Commit transaction
        db.commit()
        
        print(f"✅ Owner password reset complete for {email}")
        return True
        
    except Exception as e:
        db.rollback()
        log.error(f"Error resetting password: {e}")
        raise
    finally:
        db.close()


def main():
    """Main entry point."""
    # Check if reset is enabled
    reset_enabled = (os.getenv("RESET_OWNER_PASSWORD") or "").strip().lower()
    
    if reset_enabled not in {"true", "1", "yes", "on"}:
        log.debug("RESET_OWNER_PASSWORD not enabled, skipping reset")
        return 0
    
    try:
        log.info("Starting admin password reset...")
        env_vars = _read_env()
        _reset_admin_password(env_vars["email"], env_vars["password"])
        return 0
        
    except RuntimeError as e:
        log.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        log.error(f"Reset failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
