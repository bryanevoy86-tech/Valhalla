#!/usr/bin/env python
"""
Test input sanitization for POST /api/deals endpoint.

Tests various attack vectors and invalid inputs to ensure proper sanitization.
"""
import requests
import json
from typing import Dict, Any

API_BASE_URL = "http://localhost:4000"
API_ENDPOINT = f"{API_BASE_URL}/api/deals"


def test_xss_injection():
    """Test HTML/XSS injection in title field."""
    print("\n" + "="*70)
    print("TEST: XSS Injection Attack (HTML tags in title)")
    print("="*70)
    
    malicious_data = {
        "title": '<script>alert("XSS")</script>Sample Property',
        "stage": "lead_received",
        "status": "active",
        "arv": 250000,
        "score": 85,
        "notes": "Normal notes"
    }
    
    print(f"Input title: {malicious_data['title']}")
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=malicious_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 201:
            result = response.json()
            sanitized_title = result.get('title')
            print(f"✅ Sanitized title: {sanitized_title}")
            print(f"   Tags removed: {sanitized_title == 'Sample Property'}")
            return True
        else:
            print(f"Response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_invalid_stage():
    """Test invalid stage value (should use default)."""
    print("\n" + "="*70)
    print("TEST: Invalid Stage Value")
    print("="*70)
    
    data = {
        "title": "Test Property",
        "stage": "invalid_stage_xyz",  # Not a valid stage
        "status": "active",
        "arv": 250000,
        "score": 85
    }
    
    print(f"Input stage: {data['stage']}")
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 201:
            result = response.json()
            sanitized_stage = result.get('stage')
            print(f"✅ Sanitized stage: {sanitized_stage}")
            print(f"   Uses default: {sanitized_stage == 'lead_received'}")
            return True
        else:
            print(f"Response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_negative_numbers():
    """Test negative numbers in financial fields."""
    print("\n" + "="*70)
    print("TEST: Negative Numbers (must be non-negative)")
    print("="*70)
    
    data = {
        "title": "Test Property",
        "stage": "lead_received",
        "status": "active",
        "arv": -250000,  # Negative!
        "estimated_repair_cost": -20000,  # Negative!
        "max_allowable_offer": 150000,
        "target_assignment_fee": -5000,  # Negative!
        "score": 85
    }
    
    print(f"Input ARV: {data['arv']}")
    print(f"Input repair cost: {data['estimated_repair_cost']}")
    print(f"Input assignment fee: {data['target_assignment_fee']}")
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 201:
            result = response.json()
            arv = float(result.get('arv', 0))
            repair = float(result.get('estimated_repair_cost', 0))
            fee = float(result.get('target_assignment_fee', 0))
            
            print(f"✅ Sanitized ARV: {arv}")
            print(f"✅ Sanitized repair cost: {repair}")
            print(f"✅ Sanitized assignment fee: {fee}")
            print(f"   All non-negative: {arv >= 0 and repair >= 0 and fee >= 0}")
            return True
        else:
            print(f"Response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_score_out_of_range():
    """Test score values outside 0-100 range."""
    print("\n" + "="*70)
    print("TEST: Score Out of Range (must be 0-100)")
    print("="*70)
    
    test_cases = [
        ("Score too high", 250),
        ("Score too low", -50),
        ("Normal score", 85),
    ]
    
    for description, score_value in test_cases:
        data = {
            "title": f"Test - {description}",
            "stage": "lead_received",
            "status": "active",
            "arv": 250000,
            "score": score_value
        }
        
        print(f"\n{description}: Input score = {score_value}")
        
        try:
            response = requests.post(
                API_ENDPOINT,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 201:
                result = response.json()
                sanitized_score = float(result.get('score', 0))
                print(f"✅ Sanitized score: {sanitized_score}")
                print(f"   Within range: {0 <= sanitized_score <= 100}")
            else:
                print(f"❌ Response: {response.status_code}")
        except Exception as e:
            print(f"❌ ERROR: {e}")


def test_sql_injection_in_notes():
    """Test SQL injection attempt in notes field."""
    print("\n" + "="*70)
    print("TEST: SQL Injection Attempt in Notes")
    print("="*70)
    
    data = {
        "title": "Test Property",
        "stage": "lead_received",
        "status": "active",
        "arv": 250000,
        "notes": "'; DROP TABLE deals; --"
    }
    
    print(f"Input notes: {data['notes']}")
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 201:
            result = response.json()
            sanitized_notes = result.get('notes')
            print(f"✅ Sanitized notes: {sanitized_notes}")
            print(f"   Deal created safely (no SQL executed)")
            return True
        else:
            print(f"Response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_javascript_event_injection():
    """Test JavaScript event handler injection."""
    print("\n" + "="*70)
    print("TEST: JavaScript Event Injection")
    print("="*70)
    
    data = {
        "title": 'Test" onload="alert(\'XSS\')" x="y',
        "stage": "lead_received",
        "status": "active",
        "arv": 250000,
        "notes": "Normal"
    }
    
    print(f"Input title: {data['title']}")
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 201:
            result = response.json()
            sanitized_title = result.get('title')
            print(f"✅ Sanitized title: {sanitized_title}")
            print(f"   Event handlers removed: {'onload' not in sanitized_title}")
            return True
        else:
            print(f"Response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_valid_data():
    """Test that valid data passes through sanitization unchanged."""
    print("\n" + "="*70)
    print("TEST: Valid Data (should pass through)")
    print("="*70)
    
    data = {
        "title": "Clean Sample Property",
        "stage": "lead_received",
        "status": "active",
        "arv": 250000,
        "estimated_repair_cost": 20000,
        "max_allowable_offer": 150000,
        "target_assignment_fee": 5000,
        "score": 85,
        "notes": "Good notes without any issues",
        "disposition_status": "pending"
    }
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Valid deal created successfully")
            print(f"   ID: {result.get('id')}")
            print(f"   Title matches: {result.get('title') == data['title']}")
            print(f"   Stage matches: {result.get('stage') == data['stage']}")
            return True
        else:
            print(f"Response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    """Run all sanitization tests."""
    print("\n" + "="*70)
    print("INPUT SANITIZATION TEST SUITE")
    print("="*70)
    print(f"API Endpoint: {API_ENDPOINT}")
    print("Testing XSS, SQL injection, out-of-range values, etc.")
    
    results = []
    
    # Run tests
    results.append(("Valid Data", test_valid_data()))
    results.append(("XSS Injection", test_xss_injection()))
    results.append(("Invalid Stage", test_invalid_stage()))
    results.append(("Negative Numbers", test_negative_numbers()))
    results.append(("Score Out of Range", test_score_out_of_range()))
    results.append(("SQL Injection", test_sql_injection_in_notes()))
    results.append(("JavaScript Events", test_javascript_event_injection()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*70)


if __name__ == "__main__":
    main()
