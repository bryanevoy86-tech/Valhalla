from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.community import (
    CommunityContact,
    CommunityCampaign,
    CommunityTask,
    CommunityInteraction,
    CommunityReferral,
    CommunityTemplate,
)
from app.services.community_logic import apply_reputation_event, refresh_contact_stage


def seed_community(db: Session):
    if db.query(CommunityContact).count() > 0:
        return

    contact_1 = CommunityContact(
        full_name="Sarah Thompson",
        organization_name="Thompson Realty",
        contact_type="agent",
        region="Winnipeg",
        phone="204-555-0101",
        email="sarah@example.com",
        preferred_channel="phone",
        source="manual",
        tags="agent,referral,local",
        relationship_stage="warming",
        trust_score=72,
        consent_email=True,
        notes="Strong local agent contact. Good for off-market conversations.",
        next_follow_up_at=datetime.utcnow() - timedelta(days=1),
    )

    contact_2 = CommunityContact(
        full_name="Mike Jensen",
        organization_name="Jensen Developments",
        contact_type="contractor",
        region="Winnipeg",
        phone="204-555-0102",
        email="mike@example.com",
        preferred_channel="sms",
        source="referral",
        tags="contractor,reno,fast-response",
        relationship_stage="active",
        trust_score=84,
        consent_sms=True,
        notes="Reliable contractor lead. Good response speed.",
        next_follow_up_at=datetime.utcnow() + timedelta(days=3),
    )

    contact_3 = CommunityContact(
        full_name="Lena Brooks",
        organization_name="Brooks Capital",
        contact_type="investor",
        region="Winnipeg",
        phone="204-555-0103",
        email="lena@example.com",
        preferred_channel="email",
        source="event",
        tags="investor,private-capital",
        relationship_stage="new",
        trust_score=58,
        consent_email=True,
        notes="Met at a local business event. Needs a warm follow-up.",
        next_follow_up_at=datetime.utcnow() + timedelta(days=2),
    )

    contact_4 = CommunityContact(
        full_name="David Mercer",
        organization_name="Mercer Holdings",
        contact_type="buyer",
        region="Winnipeg",
        phone="204-555-0104",
        email="david@example.com",
        preferred_channel="phone",
        source="manual",
        tags="buyer,cash,repeat",
        relationship_stage="trusted",
        trust_score=88,
        consent_email=True,
        notes="Strong repeat buyer, but has gone quiet.",
        last_contact_at=datetime.utcnow() - timedelta(days=45),
        next_follow_up_at=datetime.utcnow() - timedelta(days=2),
    )

    db.add_all([contact_1, contact_2, contact_3, contact_4])
    db.commit()

    campaign = CommunityCampaign(
        name="Local Buyer Relationship Warmup",
        campaign_type="buyer_growth",
        region="Winnipeg",
        audience_type="buyers",
        objective="Strengthen buyer list and build repeat relationship trust.",
        status="active",
        approval_status="approved",
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    task_1 = CommunityTask(
        contact_id=contact_1.id,
        campaign_id=campaign.id,
        task_type="follow_up",
        title="Call Sarah about agent referrals",
        description="Check if she has distressed sellers or investors needing fast closings.",
        due_at=datetime.utcnow() + timedelta(days=1),
        priority="high",
        status="open",
        assigned_to="operator",
    )

    task_2 = CommunityTask(
        contact_id=contact_3.id,
        task_type="follow_up",
        title="Send Lena investor intro email",
        description="Warm introduction and request short discovery call.",
        due_at=datetime.utcnow() + timedelta(hours=12),
        priority="high",
        status="open",
        assigned_to="operator",
    )

    db.add_all([task_1, task_2])
    db.commit()

    interaction_1 = CommunityInteraction(
        contact_id=contact_1.id,
        campaign_id=campaign.id,
        interaction_type="call",
        direction="outbound",
        subject="Referral conversation",
        summary="Good call. Sarah open to sending deals if closings stay fast.",
        outcome="interested",
        sentiment="positive",
        follow_up_required=True,
        follow_up_at=datetime.utcnow() + timedelta(days=7),
        performed_by="operator",
    )

    interaction_2 = CommunityInteraction(
        contact_id=contact_2.id,
        interaction_type="sms",
        direction="outbound",
        subject="Contractor availability",
        summary="Mike confirmed availability for two quick-turn jobs next month.",
        outcome="positive_response",
        sentiment="positive",
        follow_up_required=False,
        performed_by="operator",
    )

    db.add_all([interaction_1, interaction_2])
    db.commit()

    apply_reputation_event(
        db=db,
        contact_id=contact_1.id,
        event_type="seed_positive_relationship",
        score_delta=5,
        summary="Initial strong relationship quality.",
    )

    apply_reputation_event(
        db=db,
        contact_id=contact_2.id,
        event_type="seed_reliable_operator",
        score_delta=4,
        summary="Reliable contractor reputation.",
    )

    referral = CommunityReferral(
        source_contact_id=contact_1.id,
        referral_type="seller",
        referral_status="new",
        estimated_value=12000,
        notes="Potential distressed seller intro expected.",
    )
    db.add(referral)

    refresh_contact_stage(contact_1)
    refresh_contact_stage(contact_2)
    refresh_contact_stage(contact_3)

    template_1 = CommunityTemplate(
        name="Warm Follow-Up Email",
        template_type="follow_up",
        channel="email",
        audience_type="investor",
        region="Winnipeg",
        subject="Quick follow-up, {{first_name}}",
        body="Hi {{first_name}},\n\nJust wanted to follow up and keep the conversation moving. If you're open, I'd love to set a quick time to reconnect this week.\n\nThanks,\nValhalla Legacy Inc.",
        status="approved",
        approval_status="approved",
        created_by="system",
        approved_by="system",
        notes="Simple, safe follow-up template.",
    )

    template_2 = CommunityTemplate(
        name="Buyer Reactivation SMS",
        template_type="reactivation",
        channel="sms",
        audience_type="buyer",
        region="Winnipeg",
        subject=None,
        body="Hey {{first_name}}, just checking in to see if you're still looking for good opportunities in {{region}}.",
        status="approved",
        approval_status="approved",
        created_by="system",
        approved_by="system",
        notes="Short reactivation SMS.",
    )

    db.add_all([template_1, template_2])

    db.commit()
