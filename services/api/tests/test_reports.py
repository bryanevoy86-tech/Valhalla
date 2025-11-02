"""
Smoke tests for reports endpoints.
"""

import os
import httpx

API = os.getenv("API_BASE", "http://localhost:4000")


def test_reports_summary():
    """Test the reports summary endpoint returns expected structure"""
    r = httpx.get(f"{API}/reports/summary", timeout=10)
    assert r.status_code == 200
    
    j = r.json()
    assert j.get("ok") is True
    assert "sources" in j
    assert "docs" in j
    assert "embedded" in j
    assert "embedding_coverage" in j
    
    # Verify types
    assert isinstance(j["sources"], int)
    assert isinstance(j["docs"], int)
    assert isinstance(j["embedded"], int)
    assert isinstance(j["embedding_coverage"], (int, float))
