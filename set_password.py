#!/usr/bin/env python
"""Set admin password for testing."""
import sys
import os

# Add services/api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'api'))

try:
    print("Importing modules...")
    from app.core.db import SessionLocal
    from app.users.models import UserProfile, AccountSettings
    from app.security.auth import pbkdf2_hash_password
    print("âœ… Imports successful")
    
    email = '<OWNER_EMAIL_FROM_ENV>'
    password = '<OWNER_PASSWORD_FROM_ENV>'
    
    session = SessionLocal()
    print(f"âœ… Database session created")
    
    # Check if user exists
    user = session.query(UserProfile).filter(UserProfile.email == email).first()
    if user:
        print(f"âœ… User exists: {email}")
        
        # Hash the password
        hashed_pw = pbkdf2_hash_password(password)
        print(f"âœ… Password hashed")
        
        # Update or create account settings
        account = session.query(AccountSettings).filter(AccountSettings.user_id == user.user_id).first()
        if account:
            account.password_hash = hashed_pw
            print(f"âœ… Updated existing account")
        else:
            account = AccountSettings(user_id=user.user_id, password_hash=hashed_pw)
            session.add(account)
            print(f"âœ… Created new account settings")
        
        session.commit()
        print(f"âœ… Changes committed to database")
        print(f"\nâœ… PASSWORD SET: {email} = <OWNER_PASSWORD_FROM_ENV>")
    else:
        print(f"âŒ User not found: {email}")
        users = session.query(UserProfile).all()
        if users:
            print(f"Available users:")
            for u in users:
                print(f"  - {u.email}")
        else:
            print("No users in database")
    
    session.close()
    
except Exception as e:
    print(f"âŒ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

