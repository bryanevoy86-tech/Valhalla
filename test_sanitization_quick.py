"""Quick test of sanitization module."""

import sys
from services.api.app.core.sanitization import (
    sanitize_input,
    sanitize_string_field,
    validate_fields,
    validate_numeric_field,
    sanitize_deal_data,
    validate_deal_fields,
)

def test_sanitize_input():
    """Test HTML tag removal."""
    print("\n✅ Test 1: HTML tag removal")
    result = sanitize_input("<script>alert('xss')</script>Hello")
    print(f"   Input: '<script>alert('xss')</script>Hello'")
    print(f"   Output: '{result}'")
    assert "<script>" not in result
    assert "</script>" not in result
    assert "Hello" in result
    # Note: Content inside tags (alert text) is preserved - only tags removed
    print("   PASSED ✓")

def test_sanitize_string_field():
    """Test string field sanitization with defaults."""
    print("\n✅ Test 2: String field sanitization with defaults")
    result = sanitize_string_field(None, "Default")
    print(f"   Input: None with default='Default'")
    print(f"   Output: '{result}'")
    assert result == "Default"
    print("   PASSED ✓")

def test_validate_fields():
    """Test field validation."""
    print("\n✅ Test 3: Required field validation")
    fields = {"title": "Property", "notes": ""}
    is_valid, error = validate_fields(fields, ["title", "notes"])
    print(f"   Input: {fields}")
    print(f"   Result: valid={is_valid}, error={error}")
    assert not is_valid
    assert "notes" in error.lower()
    print("   PASSED ✓")

def test_validate_numeric_field():
    """Test numeric validation."""
    print("\n✅ Test 4: Numeric field validation")
    is_valid, error = validate_numeric_field(150, min_val=0, max_val=100)
    print(f"   Input: 150 (range 0-100)")
    print(f"   Result: valid={is_valid}, error={error}")
    assert not is_valid
    assert "must be" in error.lower()
    print("   PASSED ✓")

def test_sanitize_deal_data():
    """Test deal data sanitization."""
    print("\n✅ Test 5: Deal data sanitization")
    deal_data = {
        "title": "<p>Nice Property</p>",
        "stage": "lead_received",
        "arv": 250000,
        "notes": None,
    }
    sanitized = sanitize_deal_data(deal_data)
    print(f"   Input: {deal_data}")
    print(f"   Output: {sanitized}")
    assert sanitized["title"] == "Nice Property"
    assert sanitized["arv"] == 250000
    assert sanitized["notes"] is None
    print("   PASSED ✓")

def test_validate_deal_fields():
    """Test deal field validation."""
    print("\n✅ Test 6: Deal field validation")
    deal_data = {
        "title": "Test Deal",
        "stage": "lead_received",
        "arv": 250000,
        "score": 85,
    }
    is_valid, error = validate_deal_fields(deal_data)
    print(f"   Input: {deal_data}")
    print(f"   Result: valid={is_valid}, error={error}")
    assert is_valid
    assert error is None
    print("   PASSED ✓")

def test_invalid_deal_score():
    """Test invalid deal score."""
    print("\n✅ Test 7: Invalid deal score (> 100)")
    deal_data = {
        "title": "Test Deal",
        "stage": "lead_received",
        "score": 150,
    }
    is_valid, error = validate_deal_fields(deal_data)
    print(f"   Input: {deal_data}")
    print(f"   Result: valid={is_valid}, error={error}")
    assert not is_valid
    assert "score" in error.lower()
    print("   PASSED ✓")

if __name__ == "__main__":
    print("=" * 70)
    print("SANITIZATION MODULE TEST SUITE")
    print("=" * 70)
    
    try:
        test_sanitize_input()
        test_sanitize_string_field()
        test_validate_fields()
        test_validate_numeric_field()
        test_sanitize_deal_data()
        test_validate_deal_fields()
        test_invalid_deal_score()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
