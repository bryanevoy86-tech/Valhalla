"""
PACK TT: Security Dashboard Tests
Tests for unified security dashboard aggregation.
"""

import pytest
from sqlalchemy.orm import Session
from unittest.mock import patch, AsyncMock

from app.services import security_dashboard


@pytest.fixture
def db_session(db):
    """Database session fixture."""
    return db


class TestSecurityDashboard:
    """Test security dashboard aggregation."""
    
    async def test_get_security_dashboard_structure(self, db_session):
        """Test that dashboard returns expected structure."""
        result = await security_dashboard.get_security_dashboard(db_session)
        
        assert "timestamp" in result
        assert "security_mode" in result
        assert "incidents" in result
        assert "blocklist" in result
        assert "honeypot" in result
        assert "action_requests" in result
        assert "last_update" in result
    
    async def test_dashboard_security_mode(self, db_session):
        """Test security mode in dashboard."""
        result = await security_dashboard.get_security_dashboard(db_session)
        
        assert "mode" in result["security_mode"]
        assert "updated_at" in result["security_mode"]
        assert result["security_mode"]["mode"] in ["normal", "elevated", "lockdown"]
    
    async def test_dashboard_incidents(self, db_session):
        """Test incidents summary in dashboard."""
        result = await security_dashboard.get_security_dashboard(db_session)
        
        assert "total_open" in result["incidents"]
        assert "critical" in result["incidents"]
        assert "high" in result["incidents"]
        assert "medium" in result["incidents"]
        assert "low" in result["incidents"]
    
    async def test_dashboard_blocklist(self, db_session):
        """Test blocklist summary in dashboard."""
        result = await security_dashboard.get_security_dashboard(db_session)
        
        assert "total_blocked" in result["blocklist"]
        assert "ips" in result["blocklist"]
        assert "users" in result["blocklist"]
        assert "api_keys" in result["blocklist"]
    
    async def test_dashboard_honeypot(self, db_session):
        """Test honeypot summary in dashboard."""
        result = await security_dashboard.get_security_dashboard(db_session)
        
        assert "total_instances" in result["honeypot"]
        assert "active_instances" in result["honeypot"]
        assert "recent_events" in result["honeypot"]
        assert "threats_detected" in result["honeypot"]
    
    async def test_dashboard_action_requests(self, db_session):
        """Test action requests summary in dashboard."""
        result = await security_dashboard.get_security_dashboard(db_session)
        
        assert "total_pending" in result["action_requests"]
        assert "pending_by_type" in result["action_requests"]
        assert isinstance(result["action_requests"]["pending_by_type"], dict)
