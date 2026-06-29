#!/usr/bin/env python
"""Test the login logic locally to identify the error."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'api'))

try:
    print("=" * 60)
    print("TESTING LOGIN LOGIC LOCALLY")
    print("=" * 60)
    
    # Import required modules
    print("\n1. Importing modules...")
    os.environ["VALHALLA_OWNER_USERNAME"] = "admin"
    
    from app.core.db import SessionLocal
    from app.users.models import UserProfile, AccountSettings
    from app.security.auth import pbkdf2_verify, jwt_encode
    from app.security.auth import SETTINGS
    print("✅ Imports successful")
    
    # Set credentials
    email = "bryanevoy86@gmail.com"
    password = "Dr.Doom!1"
    
    # Get database session
    print("\n2. Getting database session...")
    session = SessionLocal()
    print("✅ Database session created")
    
    # Find user
    print(f"\n3. Looking up user: {email}")
    user = session.query(UserProfile).filter(
        UserProfile.email.ilike(email)
    ).first()
    
    if not user:
        print(f"❌ User not found: {email}")
        # List all users
        users = session.query(UserProfile).all()
        print(f"Available users: {[u.email for u in users]}")
        sys.exit(1)
    
    print(f"✅ User found:")
    print(f"   ID: {user.user_id}")
    print(f"   Email: {user.email}")
    print(f"   Name: {user.first_name} {user.last_name}")
    
    # Get account settings
    print(f"\n4. Getting account settings...")
    account = session.query(AccountSettings).filter(
        AccountSettings.user_id == user.user_id
    ).first()
    
    if not account:
        print("❌ No account settings found")
        sys.exit(1)
    
    print(f"✅ Account settings found")
    print(f"   Has password hash: {bool(account.password_hash)}")
    
    # Verify password
    print(f"\n5. Verifying password...")
    is_valid = pbkdf2_verify(password, account.password_hash)
    
    if not is_valid:
        print(f"❌ Password verification failed!")
        sys.exit(1)
    
    print(f"✅ Password verified!")
    
    # Generate JWT
    print(f"\n6. Generating JWT token...")
    import time
    now = int(time.time())
    payload = {
        "sub": user.email,
        "user_id": user.user_id,
        "iat": now,
        "exp": now + SETTINGS.token_ttl_seconds,
    }
    token = jwt_encode(payload, SETTINGS.jwt_secret)
    print(f"✅ Token generated:")
    print(f"   Token: {token[:50]}...")
    print(f"   TTL: {SETTINGS.token_ttl_seconds}s")
    
    print("\n" + "=" * 60)
    print("✅ ALL CHECKS PASSED - LOGIN LOGIC WORKS LOCALLY")
    print("=" * 60)
    
    session.close()
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
