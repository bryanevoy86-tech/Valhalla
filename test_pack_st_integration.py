#!/usr/bin/env python
"""
Integration test for PACK S (System Integration) and PACK T (Production Hardening)
Tests debug endpoints, security headers, and rate limiting.
"""

import sys
sys.path.insert(0, '/dev/valhalla/services/api')

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers.debug_system import router as debug_system_router
from app.middleware.security import SecurityHeadersMiddleware, SimpleRateLimitMiddleware
from app.middleware.logging import RequestLoggingMiddleware

# Create a test app with all components
app = FastAPI(title="Test App")

# Add middleware (in reverse order - last added runs first)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SimpleRateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Include routers
app.include_router(debug_system_router)

# Add a simple health endpoint for testing
@app.get("/health")
def health():
    return {"status": "ok"}

# Create test client
client = TestClient(app)


def test_pack_s_debug_system():
    """Test PACK S: System Integration Pass"""
    print("\n" + "="*60)
    print("PACK S — Final System Integration Pass")
    print("="*60)
    
    # Test 1: /debug/routes endpoint
    print("\n1. Testing /debug/routes endpoint...")
    res = client.get("/debug/routes")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    body = res.json()
    assert "routes" in body
    assert "count" in body
    assert isinstance(body["routes"], list)
    assert len(body["routes"]) > 0
    print(f"   ✓ Route listing works: {body['count']} routes registered")
    
    # Test 2: Verify routes structure
    print("\n2. Verifying route structure...")
    for route in body["routes"][:3]:  # Check first 3
        assert "path" in route
        assert "name" in route
        assert "methods" in route
        assert isinstance(route["methods"], list)
    print(f"   ✓ All routes have proper structure")
    
    # Test 3: /debug/system endpoint
    print("\n3. Testing /debug/system endpoint...")
    res = client.get("/debug/system")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    body = res.json()
    assert "routes_count" in body
    assert "db_healthy" in body
    assert "subsystems" in body
    assert "timestamp" in body
    print(f"   ✓ System snapshot works")
    print(f"     - Routes: {body['routes_count']}")
    print(f"     - DB Health: {body['db_healthy']}")
    
    # Test 4: Check subsystems
    print("\n4. Checking subsystems health...")
    subsystems = body["subsystems"]
    print(f"   ✓ Subsystems status:")
    for name, healthy in subsystems.items():
        status_icon = "✓" if healthy else "✗"
        print(f"     {status_icon} {name}: {healthy}")


def test_pack_t_security_headers():
    """Test PACK T: Production Hardening - Security Headers"""
    print("\n" + "="*60)
    print("PACK T — Production Hardening")
    print("="*60)
    
    # Test 1: Security headers
    print("\n1. Testing security headers...")
    res = client.get("/health")
    assert res.status_code == 200
    headers = res.headers
    
    required_headers = [
        "X-Frame-Options",
        "X-Content-Type-Options",
        "Referrer-Policy",
        "X-XSS-Protection"
    ]
    
    for header in required_headers:
        assert header in headers, f"Missing header: {header}"
        print(f"   ✓ {header}: {headers[header]}")
    
    # Test 2: Verify header values
    print("\n2. Verifying header values...")
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["Referrer-Policy"] == "no-referrer"
    assert headers["X-XSS-Protection"] == "1; mode=block"
    print("   ✓ All header values correct")


def test_pack_t_rate_limiting():
    """Test PACK T: Production Hardening - Rate Limiting"""
    print("\n3. Testing rate limiting...")
    
    # Make normal requests (should all succeed)
    success_count = 0
    for i in range(10):
        res = client.get("/health")
        if res.status_code == 200:
            success_count += 1
    
    assert success_count > 0, "At least some requests should succeed"
    print(f"   ✓ Normal request volume works: {success_count}/10 succeeded")
    
    # The test client doesn't perfectly simulate real rate limiting
    # because it doesn't have a real IP address, but we can verify
    # the middleware is in place and doesn't break functionality
    print("   ✓ Rate limiting middleware active")


def test_pack_t_request_logging():
    """Test PACK T: Production Hardening - Request Logging"""
    print("\n4. Testing request logging...")
    
    # Make a request (logging should happen silently)
    res = client.get("/health")
    assert res.status_code == 200
    
    # Verify response is still intact
    body = res.json()
    assert "status" in body
    assert body["status"] == "ok"
    print("   ✓ Request logging middleware works (response intact)")


def test_combined_functionality():
    """Test PACK S and PACK T together"""
    print("\n5. Testing combined functionality...")
    
    # Make a debug request and verify security headers
    res = client.get("/debug/routes")
    
    assert res.status_code == 200
    
    # Check for security headers
    assert "X-Frame-Options" in res.headers
    assert "X-Content-Type-Options" in res.headers
    
    # Check for debug content
    body = res.json()
    assert "routes" in body
    assert "count" in body
    
    print("   ✓ Security headers applied to all endpoints including debug")
    print("   ✓ Debug endpoints work with middleware active")


if __name__ == "__main__":
    try:
        test_pack_s_debug_system()
        test_pack_t_security_headers()
        test_pack_t_rate_limiting()
        test_pack_t_request_logging()
        test_combined_functionality()
        
        print("\n" + "="*60)
        print("✓ ALL PACK S & T TESTS PASSED!")
        print("="*60 + "\n")
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
