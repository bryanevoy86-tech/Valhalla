"""
PACK TR: Security Action Tests
Tests for action request workflow and approvals.
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.security_actions import SecurityActionRequest
from app.services import security_actions


@pytest.fixture
def db_session(db):
    """Database session fixture."""
    return db


class TestSecurityActionRequest:
    """Test action request CRUD operations."""
    
    async def test_create_action_request(self, db_session):
        """Test creating an action request."""
        request = await security_actions.create_action_request(
            db_session,
            requested_by="Heimdall",
            action_type="block_entity",
            payload={"entity_type": "ip", "value": "192.168.1.100"}
        )
        assert request.status == "pending"
        assert request.requested_by == "Heimdall"
        assert request.action_type == "block_entity"
    
    async def test_list_action_requests(self, db_session):
        """Test listing action requests."""
        await security_actions.create_action_request(
            db_session, "Heimdall", "block_entity"
        )
        await security_actions.create_action_request(
            db_session, "Tyr", "set_mode"
        )
        
        result = await security_actions.list_action_requests(db_session)
        assert result["total"] == 2
        assert result["pending"] == 2
        assert len(result["items"]) == 2
    
    async def test_get_action_request(self, db_session):
        """Test getting a specific action request."""
        created = await security_actions.create_action_request(
            db_session, "Heimdall", "block_entity"
        )
        
        found = await security_actions.get_action_request(db_session, created.id)
        assert found is not None
        assert found.id == created.id
    
    async def test_approve_action(self, db_session):
        """Test approving an action request."""
        request = await security_actions.create_action_request(
            db_session, "Heimdall", "block_entity"
        )
        
        approved = await security_actions.approve_action(
            db_session, request.id, approved_by="Tyr"
        )
        assert approved.status == "approved"
        assert approved.approved_by == "Tyr"
    
    async def test_reject_action(self, db_session):
        """Test rejecting an action request."""
        request = await security_actions.create_action_request(
            db_session, "Heimdall", "block_entity"
        )
        
        rejected = await security_actions.reject_action(
            db_session,
            request.id,
            approved_by="Tyr",
            reason="Insufficient evidence"
        )
        assert rejected.status == "rejected"
        assert rejected.resolution_notes == "Insufficient evidence"
    
    async def test_list_by_status(self, db_session):
        """Test filtering action requests by status."""
        await security_actions.create_action_request(
            db_session, "Heimdall", "block_entity"
        )
        request2 = await security_actions.create_action_request(
            db_session, "Tyr", "set_mode"
        )
        
        await security_actions.approve_action(
            db_session, request2.id, approved_by="Heimdall"
        )
        
        pending = await security_actions.list_action_requests(
            db_session, status="pending"
        )
        assert pending["pending"] == 1
