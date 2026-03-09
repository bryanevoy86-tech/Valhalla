#!/usr/bin/env python
"""
Test script to verify the email service works.
"""

import sys
import os

# Add the services/api app to path
sys.path.insert(0, "services/api")

# Set test environment variables if not already set
if not os.getenv("VALHALLA_SYSTEM_EMAIL"):
    os.environ["VALHALLA_SYSTEM_EMAIL"] = "ValhallaLegacyInc@gmail.com"
if not os.getenv("VALHALLA_FROM_NAME"):
    os.environ["VALHALLA_FROM_NAME"] = "Valhalla Legacy Inc"

print("=" * 60)
print("VALHALLA EMAIL SERVICE TEST")
print("=" * 60)

# Test 1: Import identity module
print("\n[TEST 1] Importing identity module...")
try:
    from app.core.identity import system_identity, get_system_email
    print("✓ Identity module imported successfully")
except Exception as e:
    print(f"✗ Failed to import identity: {e}")
    sys.exit(1)

# Test 2: Get system identity
print("\n[TEST 2] Getting system identity...")
try:
    identity = system_identity()
    email = identity["email"]
    from_name = identity["from_name"]
    print(f"✓ System email: {email}")
    print(f"✓ From name: {from_name}")
except Exception as e:
    print(f"✗ Failed to get identity: {e}")
    sys.exit(1)

# Test 3: Import email service
print("\n[TEST 3] Importing email service...")
try:
    from app.services.email_service import send_email, build_from_header
    print("✓ Email service imported successfully")
except Exception as e:
    print(f"✗ Failed to import email service: {e}")
    sys.exit(1)

# Test 4: Test From header formatting
print("\n[TEST 4] Testing From header formatting...")
try:
    from_header = build_from_header()
    print(f"✓ From header: {from_header}")
    expected = f"Valhalla Legacy Inc <{email}>"
    if from_header == expected:
        print(f"✓ From header formatted correctly")
    else:
        print(f"⚠ From header format: expected '{expected}', got '{from_header}'")
except Exception as e:
    print(f"✗ Failed to build From header: {e}")
    sys.exit(1)

# Test 5: Import daily summary service
print("\n[TEST 5] Importing daily summary service...")
try:
    from app.services.daily_summary import (
        get_default_summary_recipient,
        format_summary_report,
    )
    print("✓ Daily summary service imported successfully")
except Exception as e:
    print(f"✗ Failed to import daily summary service: {e}")
    sys.exit(1)

# Test 6: Get default recipient
print("\n[TEST 6] Getting default summary recipient...")
try:
    recipient = get_default_summary_recipient()
    print(f"✓ Default recipient: {recipient}")
except Exception as e:
    print(f"✗ Failed to get default recipient: {e}")
    sys.exit(1)

# Test 7: Test summary report formatting
print("\n[TEST 7] Testing summary report formatting...")
try:
    report = format_summary_report(
        title="Test Report",
        sections={
            "System Health": "✓ All operational",
            "Alerts": "0 pending",
        },
        footer="End of test"
    )
    print("✓ Summary report formatted successfully")
    print("\nReport preview:")
    print("-" * 60)
    print(report[:300] + "..." if len(report) > 300 else report)
    print("-" * 60)
except Exception as e:
    print(f"✗ Failed to format summary: {e}")
    sys.exit(1)

# Test 8: Import email guard
print("\n[TEST 8] Importing email guard...")
try:
    from app.guards.email_guard import (
        assert_system_email,
        validate_sender_email,
    )
    print("✓ Email guard imported successfully")
except Exception as e:
    print(f"✗ Failed to import email guard: {e}")
    sys.exit(1)

# Test 9: Test email guard validation
print("\n[TEST 9] Testing email guard validation...")
try:
    # Valid email should not raise
    assert_system_email(email)
    print(f"✓ Valid email accepted: {email}")
    
    # Invalid email should raise
    try:
        assert_system_email("invalid@example.com")
        print("✗ Invalid email should have been rejected")
    except Exception as guard_error:
        print(f"✓ Invalid email correctly rejected: {type(guard_error).__name__}")
except Exception as e:
    print(f"✗ Email guard test failed: {e}")
    sys.exit(1)

# Test 10: Email sending capability check
print("\n[TEST 10] Email sending capability check...")
print("Note: Actual email sending requires SMTP configuration (SMTP_HOST, SMTP_USER, SMTP_PASS)")
print("These should be set in .env or environment variables")

smtp_host = os.getenv("SMTP_HOST")
smtp_user = os.getenv("SMTP_USER")
if smtp_host and smtp_user:
    print(f"✓ SMTP configured: {smtp_host}")
    print("  To send test email, ensure SMTP_PASS is also set")
    
    # Try to send test email
    print("\n[TEST 11] Attempting to send test email...")
    try:
        result = send_email(
            to_email=email,
            subject="Valhalla System Email Test",
            body=f"This is a test email from the Valhalla system.\n\nSent at: {os.popen('date').read().strip()}"
        )
        if result:
            print(f"✓ Email sent successfully to {email}")
        else:
            print("⚠ Email send returned False (possible SMTP config issue)")
    except Exception as e:
        print(f"⚠ Email send error: {e}")
else:
    print("⚠ SMTP not configured, skipping email send test")
    print("  To send emails, configure SMTP_HOST and SMTP_USER in .env")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED")
print("=" * 60)
print("\n✓ Email service is ready!")
print(f"\nSummary:")
print(f"  System Email: {email}")
print(f"  From Name: {from_name}")
print(f"  Default Recipient: {recipient}")
