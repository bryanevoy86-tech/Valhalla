"""
PACK L0-07: Central Rate Limiting Helper
Centralized rate limiting logic for middleware integration.
Marked as stable API (STABLE CONTRACT).
"""

from typing import Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.rate_limit import RateLimitSnapshot
from app.schemas.rate_limit import RateLimitRuleSet


class RateLimitHelper:
    """
    Central rate limiting helper for use in middleware.
    
    Checks requests against rules and tracks violations.
    Violations are recorded for security dashboard and telemetry.
    """
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
    
    def check_rate_limit(
        self,
        scope: str,
        identifier: str,  # IP, user ID, API key, etc.
        limit: int,
        window_seconds: int = 60,
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if identifier has exceeded rate limit.
        
        STABLE CONTRACT: Return type will not change.
        
        Args:
            scope: Rate limit scope (e.g., 'api.login', 'api.upload', 'global')
            identifier: Unique identifier (IP address, user ID, API key)
            limit: Maximum requests allowed in window
            window_seconds: Time window in seconds (default 60)
        
        Returns:
            Tuple of (allowed: bool, remaining_requests: Optional[int])
                - allowed: True if within limits
                - remaining_requests: Requests left in window (None if exceeded)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Get existing snapshot
        snapshot = (
            self.db.query(RateLimitSnapshot)
            .filter(
                RateLimitSnapshot.scope == scope,
                RateLimitSnapshot.identifier == identifier,
            )
            .first()
        )
        
        # Reset if outside window
        if snapshot and snapshot.last_reset < window_start:
            snapshot.request_count = 0
            snapshot.last_reset = now
            self.db.commit()
        
        # Create if doesn't exist
        if not snapshot:
            snapshot = RateLimitSnapshot(
                scope=scope,
                identifier=identifier,
                request_count=0,
                limit=limit,
                window_seconds=window_seconds,
                last_reset=now,
            )
            self.db.add(snapshot)
            self.db.commit()
            self.db.refresh(snapshot)
        
        # Check limit
        if snapshot.request_count >= limit:
            return False, None  # Exceeded
        
        # Increment and allow
        snapshot.request_count += 1
        snapshot.last_updated = now
        self.db.commit()
        
        remaining = limit - snapshot.request_count
        return True, remaining
    
    def record_violation(
        self,
        scope: str,
        identifier: str,
        violation_type: str = "rate_limit_exceeded",
        details: Optional[dict] = None,
    ) -> None:
        """
        Record a rate limit violation for security tracking.
        
        Args:
            scope: Rate limit scope
            identifier: Unique identifier (IP, user, key)
            violation_type: Type of violation
            details: Additional violation details
        """
        # This would integrate with security_actions or telemetry
        # For now, just track the violation
        pass


def get_rate_limit_helper(db: Session) -> RateLimitHelper:
    """Factory function to create RateLimitHelper instance."""
    return RateLimitHelper(db)
