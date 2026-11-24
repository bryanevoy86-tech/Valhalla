"""
Smoke tests for reports endpoints.
"""




def test_reports_summary(legacy_http_client):
    client, _ = legacy_http_client
    """Test the reports summary endpoint returns expected structure"""
    r = client.get("/reports/summary")
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
