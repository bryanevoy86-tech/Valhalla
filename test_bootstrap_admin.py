#!/usr/bin/env python
"""
Quick test of bootstrap admin user creation.
Run this to verify bootstrap works before starting the full backend.
"""

import os
import sys
from pathlib import Path

# Load .env first
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Add app to path
sys.path.insert(0, str(Path(__file__).parent / "services" / "api"))

# Set defaults if not in .env
os.environ.setdefault("DATABASE_URL", "sqlite:///./valhalla_local.db")
os.environ.setdefault("VALHALLA_JWT_SECRET", "dev-secret-key-test")
os.environ.setdefault("VALHALLA_OWNER_USERNAME", "admin")
os.environ.setdefault("VALHALLA_OWNER_PASSWORD", "admin-change-me")
os.environ.setdefault("BOOTSTRAP_ADMIN_EMAIL", "bryanevoy86@gmail.com")
os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", "DrDoom!1")

from app.core.db import SessionLocal, Base, engine
from app.services.bootstrap_admin import bootstrap_admin_user

print("=" * 80)
print("BOOTSTRAP ADMIN TEST")
print("=" * 80)

# Create tables
print("\n[1/3] Creating database tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created/verified")
except Exception as e:
    print(f"✗ Error creating tables: {e}")
    sys.exit(1)

# Run bootstrap
print("\n[2/3] Running bootstrap admin creation...")
db = SessionLocal()
try:
    result = bootstrap_admin_user(db)
    print(f"✓ Bootstrap result: {result['status']}")
    print(f"  Email: {result.get('email')}")
    print(f"  Detail: {result['detail']}")
except Exception as e:
    print(f"✗ Error during bootstrap: {e}")
    sys.exit(1)
finally:
    db.close()

# Verify user was created
print("\n[3/3] Verifying user creation...")
db = SessionLocal()
try:
    from app.users.models import UserProfile, AccountSettings
    
    email = os.getenv("BOOTSTRAP_ADMIN_EMAIL")
    user = db.query(UserProfile).filter(UserProfile.email == email).first()
    
    if user:
        settings = db.query(AccountSettings).filter(AccountSettings.user_id == user.user_id).first()
        print(f"✓ User found: {user.first_name} {user.last_name} ({email})")
        print(f"  User ID: {user.user_id}")
        print(f"  Has password hash: {bool(settings and settings.password_hash)}")
        print(f"  Created: {user.created_at}")
    else:
        print(f"✗ User not found: {email}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error verifying user: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()

print("\n" + "=" * 80)
print("✓ BOOTSTRAP TEST PASSED - User is ready for login")
print("=" * 80)
print("\nNext: Test login with:")
print(f"  Email: {email}")
print(f"  Password: {os.getenv('BOOTSTRAP_ADMIN_PASSWORD')}")
print("\nAttempt login: POST http://localhost:4000/ops/token")
print("  Form data: username={email}, password={password}")
