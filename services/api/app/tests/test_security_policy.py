"""
PACK TQ: Security Policy Tests
Tests for security policy and blocklist management.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.security_policy import SecurityPolicy, BlockedEntity
from app.services import security_policy


@pytest.fixture
def db_session(db):
    """Database session fixture."""
    return db


class TestSecurityPolicy:
    """Test security policy CRUD operations."""
    
    async def test_ensure_policy_row_creates_default(self, db_session):
        """Test that ensure_policy_row creates a default policy."""
        policy = await security_policy.ensure_policy_row(db_session)
        assert policy is not None
        assert policy.default_mode == "normal"
        assert policy.auto_elevate == False
    
    async def test_get_policy(self, db_session):
        """Test getting security policy."""
        await security_policy.ensure_policy_row(db_session)
        policy = await security_policy.get_policy(db_session)
        assert policy is not None
        assert policy.id == 1
    
    async def test_update_policy(self, db_session):
        """Test updating security policy."""
        await security_policy.ensure_policy_row(db_session)
        updated = await security_policy.update_policy(
            db_session,
            default_mode="elevated",
            auto_elevate=True,
            max_failed_auth=10
        )
        assert updated.default_mode == "elevated"
        assert updated.auto_elevate == True
        assert updated.max_failed_auth == 10


class TestBlockedEntity:
    """Test blocked entity management."""
    
    async def test_create_block(self, db_session):
        """Test creating a blocked entity."""
        block = await security_policy.create_block(
            db_session,
            entity_type="ip",
            value="192.168.1.100",
            reason="Suspicious activity",
            expires_at=None
        )
        assert block.entity_type == "ip"
        assert block.value == "192.168.1.100"
        assert block.active == True
    
    async def test_list_blocks(self, db_session):
        """Test listing blocked entities."""
        await security_policy.create_block(
            db_session, "ip", "192.168.1.100", "test"
        )
        await security_policy.create_block(
            db_session, "user", "attacker@test.com", "test"
        )
        
        result = await security_policy.list_blocks(db_session, active_only=True)
        assert result["total"] == 2
        assert result["active"] == 2
        assert len(result["items"]) == 2
    
    async def test_deactivate_block(self, db_session):
        """Test deactivating a blocked entity."""
        block = await security_policy.create_block(
            db_session, "ip", "192.168.1.100", "test"
        )
        deactivated = await security_policy.deactivate_block(db_session, block.id)
        assert deactivated.active == False
    
    async def test_cleanup_expired_blocks(self, db_session):
        """Test cleanup of expired blocks."""
        now = datetime.utcnow()
        past = now - timedelta(hours=1)
        
        block = await security_policy.create_block(
            db_session,
            entity_type="ip",
            value="192.168.1.100",
            reason="expired",
            expires_at=past
        )
        
        cleaned = await security_policy.cleanup_expired_blocks(db_session)
        assert cleaned == 1
        
        recheck = db_session.query(BlockedEntity).filter(
            BlockedEntity.id == block.id
        ).first()
        assert recheck.active == False
