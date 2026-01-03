"""Smoke tests for Valhalla Governance Core."""
import sys
from pathlib import Path

# Add parent directories to path for imports (backup in case conftest doesn't run first)
backend_path = str(Path(__file__).parent.parent)
root_path = str(Path(__file__).parent.parent.parent)

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

# Get client fixture from conftest
# The app is imported in conftest.py


def test_healthz(client):
    """Test basic health check."""
    r = client.get("/core/healthz")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_cone_state(client):
    """Test cone state endpoint."""
    r = client.get("/core/cone/state")
    assert r.status_code == 200
    body = r.json()
    assert "band" in body
    assert "reason" in body
    assert "updated_at_utc" in body


def test_cone_decide_allows_wholesaling_run(client):
    """Test Cone allows BORING class wholesaling to run."""
    r = client.get("/core/cone/decide", params={"engine": "wholesaling", "action": "run"})
    assert r.status_code == 200
    assert r.json()["allowed"] is True


def test_cone_decide_denies_fx_scale(client):
    """Test Cone denies OPPORTUNISTIC class FX arbitrage from scaling."""
    r = client.get("/core/cone/decide", params={"engine": "fx_arbitrage", "action": "scale"})
    assert r.status_code == 200
    assert r.json()["allowed"] is False


def test_visibility_summary(client):
    """Test phone-first visibility endpoint."""
    r = client.get("/core/visibility/summary")
    assert r.status_code == 200
    body = r.json()
    assert "cone" in body
    assert "engines" in body
    assert "jobs" in body
    assert len(body["engines"]) == 19  # All Canon engines


def test_alerts_endpoint(client):
    """Test alerts dashboard endpoint."""
    r = client.get("/core/alerts")
    assert r.status_code == 200
    body = r.json()
    assert "cone" in body
    assert "jobs" in body
    assert "engine_registry" in body
    assert "warnings" in body
    assert "audit_tail" in body


def test_cone_persistence(client):
    """Test Cone state persists across calls."""
    from app.core_gov.cone.service import set_cone_state, get_cone_state
    from app.core_gov.canon.canon import ConeBand
    
    # Set to different band
    original_band = get_cone_state().band
    try:
        set_cone_state(ConeBand.A_EXPANSION, "Test persistence")
        
        # Verify it was set
        state = get_cone_state()
        assert state.band == ConeBand.A_EXPANSION
        assert state.reason == "Test persistence"
    finally:
        # Restore original
        set_cone_state(original_band, "Reset to original")
