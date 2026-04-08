#!/usr/bin/env python
"""Create community database tables directly."""
from app.core.db import Base, engine
from app.models.community import (
    CommunityContact,
    CommunityInteraction,
    CommunityCampaign,
    CommunityTask,
    CommunityReferral,
    CommunityReputationEvent,
    CommunityTemplate,
    CommunityMessageLog,
)

# Create all community tables
Base.metadata.create_all(engine)
print("✓ Community database tables created successfully")
print("  - community_contacts")
print("  - community_interactions")
print("  - community_campaigns")
print("  - community_tasks")
print("  - community_referrals")
print("  - community_reputation_events")
print("  - community_templates")
print("  - community_message_logs")
