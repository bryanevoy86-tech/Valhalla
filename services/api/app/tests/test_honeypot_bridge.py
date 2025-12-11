"""
PACK TS: Honeypot Bridge Tests
Tests for honeypot instance and event management.
"""

import pytest
from sqlalchemy.orm import Session

from app.models.honeypot_bridge import HoneypotInstance, HoneypotEvent
from app.services import honeypot_bridge


@pytest.fixture
def db_session(db):
    """Database session fixture."""
    return db


class TestHoneypotInstance:
    """Test honeypot instance management."""
    
    async def test_create_instance(self, db_session):
        """Test creating a honeypot instance."""
        instance = await honeypot_bridge.create_instance(
            db_session,
            name="SSH Trap",
            honeypot_type="ssh",
            location="us-east-1",
            metadata={"version": "1.0"}
        )
        assert instance.name == "SSH Trap"
        assert instance.honeypot_type == "ssh"
        assert instance.api_key is not None
        assert len(instance.api_key) > 0
    
    async def test_get_instance_by_api_key(self, db_session):
        """Test retrieving instance by API key."""
        created = await honeypot_bridge.create_instance(
            db_session, "Web Trap", "web"
        )
        
        found = await honeypot_bridge.get_instance_by_api_key(
            db_session, created.api_key
        )
        assert found is not None
        assert found.id == created.id
    
    async def test_list_instances(self, db_session):
        """Test listing honeypot instances."""
        await honeypot_bridge.create_instance(db_session, "SSH Trap", "ssh")
        await honeypot_bridge.create_instance(db_session, "Web Trap", "web")
        
        result = await honeypot_bridge.list_instances(db_session, active_only=True)
        assert result["total"] == 2
        assert result["active_instances"] == 2
        assert len(result["items"]) == 2
    
    async def test_deactivate_instance(self, db_session):
        """Test deactivating a honeypot instance."""
        instance = await honeypot_bridge.create_instance(
            db_session, "SSH Trap", "ssh"
        )
        
        deactivated = await honeypot_bridge.deactivate_instance(
            db_session, instance.id
        )
        assert deactivated.active == False


class TestHoneypotEvent:
    """Test honeypot event recording."""
    
    async def test_record_event(self, db_session):
        """Test recording a honeypot event."""
        instance = await honeypot_bridge.create_instance(
            db_session, "SSH Trap", "ssh"
        )
        
        event = await honeypot_bridge.record_event(
            db_session,
            honeypot_id=instance.id,
            source_ip="203.0.113.45",
            event_type="auth_attempt",
            payload={"username": "admin", "password": "test"}
        )
        assert event.source_ip == "203.0.113.45"
        assert event.event_type == "auth_attempt"
        assert event.processed == False
    
    async def test_list_events(self, db_session):
        """Test listing honeypot events."""
        instance = await honeypot_bridge.create_instance(
            db_session, "SSH Trap", "ssh"
        )
        
        await honeypot_bridge.record_event(
            db_session, instance.id, "203.0.113.45", "connection"
        )
        await honeypot_bridge.record_event(
            db_session, instance.id, "203.0.113.46", "auth_attempt"
        )
        
        result = await honeypot_bridge.list_events(db_session)
        assert result["total"] == 2
        assert result["unprocessed"] == 2
        assert len(result["items"]) == 2
    
    async def test_mark_event_processed(self, db_session):
        """Test marking event as processed."""
        instance = await honeypot_bridge.create_instance(
            db_session, "SSH Trap", "ssh"
        )
        
        event = await honeypot_bridge.record_event(
            db_session, instance.id, "203.0.113.45", "connection"
        )
        
        processed = await honeypot_bridge.mark_event_processed(
            db_session, event.id
        )
        assert processed.processed == True
    
    async def test_list_unprocessed_only(self, db_session):
        """Test filtering for unprocessed events."""
        instance = await honeypot_bridge.create_instance(
            db_session, "SSH Trap", "ssh"
        )
        
        event1 = await honeypot_bridge.record_event(
            db_session, instance.id, "203.0.113.45", "connection"
        )
        event2 = await honeypot_bridge.record_event(
            db_session, instance.id, "203.0.113.46", "auth_attempt"
        )
        
        await honeypot_bridge.mark_event_processed(db_session, event1.id)
        
        result = await honeypot_bridge.list_events(
            db_session, unprocessed_only=True
        )
        assert result["unprocessed"] == 1
