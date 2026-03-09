#!/usr/bin/env python
"""
Integration test for PACK W (System Completion Metadata)
Tests system status, completion flag, and pack registry.
"""

import sys
sys.path.insert(0, '/dev/valhalla/services/api')

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models.base import Base
from app.models.system_metadata import SystemMetadata
from app.core.db import get_db
from app.routers.system_status import router as system_status_router

# Create in-memory test database
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create all tables
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test app
app = FastAPI(title="Test PACK W")

def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
app.include_router(system_status_router)

# Test client
client = TestClient(app)


def test_pack_w_system_status():
    """Test PACK W: System Completion Metadata"""
    print("\n" + "="*70)
    print("PACK W — System Completion Confirmation / Metadata")
    print("="*70)
    
    # Test 1: Get system status
    print("\n1. Testing GET /system/status/...")
    res = client.get("/system/status/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    body = res.json()
    print(f"   ✓ Status endpoint responds with 200 OK")
    
    # Test 2: Verify response structure
    print("\n2. Verifying response structure...")
    assert "version" in body
    assert "backend_complete" in body
    assert "packs" in body
    assert "summary" in body
    assert "extra" in body
    print(f"   ✓ Response has all required fields")
    
    # Test 3: Check version format
    print("\n3. Checking version format...")
    version = body["version"]
    parts = version.split(".")
    assert len(parts) == 3, f"Version should be semantic (major.minor.patch), got {version}"
    print(f"   ✓ Version format valid: {version}")
    
    # Test 4: Check pack list
    print("\n4. Checking pack list...")
    packs = body["packs"]
    assert len(packs) == 16, f"Expected 16 packs, got {len(packs)}"
    print(f"   ✓ All 16 packs present")
    
    # Test 5: Verify pack IDs
    print("\n5. Verifying pack IDs...")
    pack_ids = [p["id"] for p in packs]
    expected_ids = ["H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W"]
    for pack_id in expected_ids:
        assert pack_id in pack_ids, f"Pack {pack_id} missing"
    print(f"   ✓ All expected packs (H-W) present")
    
    # Test 6: Check pack structure
    print("\n6. Checking pack structure...")
    for pack in packs:
        assert "id" in pack
        assert "name" in pack
        assert "status" in pack
        assert pack["status"] == "installed"
    print(f"   ✓ All packs have proper structure")
    
    # Test 7: List packs
    print("\n7. Listing packs by domain:")
    professional_packs = [p for p in packs if p["id"] in "HIJKLMNOPQR"]
    system_packs = [p for p in packs if p["id"] in "STUVW"]
    print(f"   Professional Packs (H-R): {len(professional_packs)}")
    for p in professional_packs:
        print(f"     - {p['id']}: {p['name']}")
    print(f"   System Packs (S-W): {len(system_packs)}")
    for p in system_packs:
        print(f"     - {p['id']}: {p['name']}")
    
    # Test 8: Check metadata
    print("\n8. Checking metadata...")
    assert body["extra"]["notes"]
    assert body["extra"]["updated_at"]
    print(f"   ✓ Metadata includes notes and timestamps")
    
    # Test 9: Mark backend complete
    print("\n9. Testing mark backend complete...")
    res = client.post(
        "/system/status/complete",
        json={"notes": "Backend fully wired and tested"}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["backend_complete"] is True
    print(f"   ✓ Backend marked as complete")
    
    # Test 10: Verify completion persisted
    print("\n10. Verifying completion persisted...")
    res = client.get("/system/status/")
    body = res.json()
    assert body["backend_complete"] is True
    print(f"    ✓ Completion status persisted")
    
    # Test 11: Mark backend incomplete
    print("\n11. Testing mark backend incomplete...")
    res = client.post(
        "/system/status/incomplete",
        json={"notes": "Found issue, reverting to dev"}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["backend_complete"] is False
    print(f"    ✓ Backend marked as incomplete")
    
    # Test 12: Get summary (lightweight)
    print("\n12. Testing lightweight summary...")
    res = client.get("/system/status/summary")
    assert res.status_code == 200
    body = res.json()
    assert body["total_packs"] == 16
    assert body["installed_packs"] == 16
    print(f"    ✓ Summary endpoint: {body['total_packs']} total, {body['installed_packs']} installed")
    
    # Test 13: List packs endpoint
    print("\n13. Testing list packs endpoint...")
    res = client.get("/system/status/packs")
    assert res.status_code == 200
    body = res.json()
    assert len(body["packs"]) == 16
    print(f"    ✓ Packs endpoint lists all 16 packs")
    
    # Test 14: Get specific pack
    print("\n14. Testing get specific pack...")
    res = client.get("/system/status/packs/W")
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == "W"
    assert body["name"] == "System Completion Metadata"
    print(f"    ✓ Pack W retrieved: {body['name']}")
    
    # Test 15: Case insensitive pack lookup
    print("\n15. Testing case-insensitive pack lookup...")
    res = client.get("/system/status/packs/h")
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == "H"
    print(f"    ✓ Case-insensitive lookup works")
    
    # Test 16: Non-existent pack returns 404
    print("\n16. Testing 404 for invalid pack...")
    res = client.get("/system/status/packs/ZZ")
    assert res.status_code == 404
    print(f"    ✓ Invalid pack returns 404")
    
    # Test 17: Summary text
    print("\n17. Checking summary description...")
    res = client.get("/system/status/")
    body = res.json()
    summary = body["summary"]
    assert "professional" in summary.lower()
    assert "valhalla" in summary.lower()
    assert "management" in summary.lower()
    print(f"    ✓ Summary describes backend functionality")
    
    # Test 18: Complete state transitions
    print("\n18. Testing complete→incomplete→complete transitions...")
    # Mark complete
    client.post("/system/status/complete", json={"notes": "Transition test 1"})
    res = client.get("/system/status/")
    assert res.json()["backend_complete"] is True
    
    # Mark incomplete
    client.post("/system/status/incomplete", json={"notes": "Transition test 2"})
    res = client.get("/system/status/")
    assert res.json()["backend_complete"] is False
    
    # Mark complete again
    client.post("/system/status/complete", json={"notes": "Transition test 3"})
    res = client.get("/system/status/")
    assert res.json()["backend_complete"] is True
    print(f"    ✓ State transitions working correctly")
    
    # Test 19: Notes update
    print("\n19. Testing notes update...")
    res = client.post(
        "/system/status/complete",
        json={"notes": "Updated notes at " + "2025-12-05"}
    )
    body = res.json()
    assert "Updated notes" in body["extra"]["notes"]
    print(f"    ✓ Notes updated correctly")
    
    # Test 20: Version update
    print("\n20. Testing version update...")
    res = client.post(
        "/system/status/complete",
        json={"version": "1.1.0", "notes": "Version bump"}
    )
    body = res.json()
    assert body["version"] == "1.1.0"
    print(f"    ✓ Version updated to {body['version']}")


def test_pack_w_endpoints_exist():
    """Verify all PACK W endpoints are available."""
    print("\n" + "="*70)
    print("PACK W Endpoint Verification")
    print("="*70)
    
    endpoints = [
        ("GET", "/system/status/", "Full system status"),
        ("GET", "/system/status/summary", "Lightweight summary"),
        ("POST", "/system/status/complete", "Mark backend complete"),
        ("POST", "/system/status/incomplete", "Mark backend incomplete"),
        ("GET", "/system/status/packs", "List all packs"),
        ("GET", "/system/status/packs/H", "Get specific pack"),
    ]
    
    print("\nEndpoints:")
    for method, path, desc in endpoints:
        if method == "GET":
            res = client.get(path)
        else:
            res = client.post(path)
        status = "✓" if res.status_code < 500 else "✗"
        print(f"   {status} {method:4} {path:40} - {desc}")


if __name__ == "__main__":
    try:
        test_pack_w_system_status()
        test_pack_w_endpoints_exist()
        
        print("\n" + "="*70)
        print("✓ ALL PACK W TESTS PASSED!")
        print("="*70 + "\n")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
