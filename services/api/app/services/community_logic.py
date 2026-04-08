from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.community import (
    CommunityContact,
    CommunityInteraction,
    CommunityTask,
    CommunityReferral,
    CommunityReputationEvent,
)


def clamp_score(value: int) -> int:
    return max(0, min(100, value))


def apply_reputation_event(
    db: Session,
    contact_id: Optional[int],
    event_type: str,
    score_delta: int,
    summary: str,
):
    event = CommunityReputationEvent(
        contact_id=contact_id,
        event_type=event_type,
        score_delta=score_delta,
        summary=summary,
    )
    db.add(event)

    if contact_id:
        contact = db.query(CommunityContact).filter(CommunityContact.id == contact_id).first()
        if contact:
            contact.trust_score = clamp_score((contact.trust_score or 50) + score_delta)

    return event


def score_interaction_effect(interaction_type: str, outcome: Optional[str], sentiment: Optional[str]) -> int:
    score = 0

    positive_interactions = {"meeting", "referral", "event", "call", "email", "sms"}
    if interaction_type in positive_interactions:
        score += 1

    if outcome in {"interested", "follow_up", "referred", "closed", "positive_response"}:
        score += 4
    elif outcome in {"no_answer", "delayed"}:
        score += 0
    elif outcome in {"not_interested", "complaint", "negative_response"}:
        score -= 5

    if sentiment == "positive":
        score += 3
    elif sentiment == "neutral":
        score += 0
    elif sentiment == "negative":
        score -= 4

    return score


def refresh_contact_stage(contact: CommunityContact):
    score = contact.trust_score or 50
    if score >= 85:
        contact.relationship_stage = "trusted"
    elif score >= 65:
        contact.relationship_stage = "active"
    elif score >= 45:
        contact.relationship_stage = "warming"
    else:
        contact.relationship_stage = "new"


def get_next_best_action(contact: CommunityContact) -> dict:
    now = datetime.utcnow()

    if contact.next_follow_up_at and contact.next_follow_up_at <= now:
        return {
            "action": "follow_up_now",
            "priority": "high",
            "reason": "Follow-up is due now or overdue.",
        }

    if contact.relationship_stage == "new":
        return {
            "action": "make_first_contact",
            "priority": "high",
            "reason": "New contact has not been developed yet.",
        }

    if contact.relationship_stage == "warming":
        return {
            "action": "build_relationship",
            "priority": "high",
            "reason": "Contact is warming and should be moved toward active trust.",
        }

    if contact.relationship_stage == "active" and (contact.trust_score or 0) >= 75:
        return {
            "action": "ask_for_referral_or_opportunity",
            "priority": "medium",
            "reason": "Active contact is trusted enough for opportunity expansion.",
        }

    if contact.relationship_stage == "trusted":
        return {
            "action": "maintain_trust",
            "priority": "medium",
            "reason": "Trusted contact should receive consistent relationship maintenance.",
        }

    return {
        "action": "review_contact",
        "priority": "low",
        "reason": "No specific action detected. Review manually.",
    }


def calculate_contact_heat(contact: CommunityContact) -> int:
    now = datetime.utcnow()
    score = contact.trust_score or 50

    if contact.next_follow_up_at:
        if contact.next_follow_up_at <= now:
            score += 15
        elif contact.next_follow_up_at <= now + timedelta(days=3):
            score += 8

    if contact.relationship_stage == "trusted":
        score += 10
    elif contact.relationship_stage == "active":
        score += 6
    elif contact.relationship_stage == "warming":
        score += 3

    return clamp_score(score)


# STALE RELATIONSHIP DETECTION & AUTOMATION

STALE_DAYS_BY_STAGE = {
    "new": 5,
    "warming": 7,
    "active": 14,
    "trusted": 30,
    "dormant": 45,
}

DECAY_BY_STAGE = {
    "new": -2,
    "warming": -3,
    "active": -4,
    "trusted": -2,
    "dormant": -1,
}


def get_stale_cutoff(stage: str) -> datetime:
    days = STALE_DAYS_BY_STAGE.get(stage or "new", 7)
    return datetime.utcnow() - timedelta(days=days)


def is_contact_stale(contact: CommunityContact) -> bool:
    if contact.last_contact_at is None:
        return True
    cutoff = get_stale_cutoff(contact.relationship_stage)
    return contact.last_contact_at < cutoff


def decay_contact_if_stale(db: Session, contact: CommunityContact) -> bool:
    if not is_contact_stale(contact):
        return False

    delta = DECAY_BY_STAGE.get(contact.relationship_stage or "new", -2)

    apply_reputation_event(
        db=db,
        contact_id=contact.id,
        event_type="relationship_decay",
        score_delta=delta,
        summary=f"Automatic decay applied because contact became stale at stage '{contact.relationship_stage}'.",
    )

    refresh_contact_stage(contact)
    return True


def has_open_follow_up_task(db: Session, contact_id: int) -> bool:
    existing = (
        db.query(CommunityTask)
        .filter(CommunityTask.contact_id == contact_id)
        .filter(CommunityTask.task_type == "follow_up")
        .filter(CommunityTask.status.in_(["open", "in_progress"]))
        .first()
    )
    return existing is not None


def create_follow_up_task_if_missing(
    db: Session,
    contact: CommunityContact,
    reason: str,
    due_in_days: int = 1,
    priority: str = "high",
    assigned_to: str | None = "operator",
) -> CommunityTask | None:
    if has_open_follow_up_task(db, contact.id):
        return None

    task = CommunityTask(
        contact_id=contact.id,
        task_type="follow_up",
        title=f"Follow up with {contact.full_name}",
        description=reason,
        due_at=datetime.utcnow() + timedelta(days=due_in_days),
        priority=priority,
        status="open",
        assigned_to=assigned_to,
    )
    db.add(task)
    return task


def process_contact_automation(db: Session, contact: CommunityContact) -> dict:
    stale = is_contact_stale(contact)
    decayed = False
    task_created = False

    if stale:
        decayed = decay_contact_if_stale(db, contact) or False

        task = create_follow_up_task_if_missing(
            db=db,
            contact=contact,
            reason="This relationship has gone stale and needs a personal follow-up.",
            due_in_days=1,
            priority="high",
            assigned_to=contact.owner_user_id or "operator",
        )
        task_created = task is not None

    refresh_contact_stage(contact)

    return {
        "contact_id": contact.id,
        "full_name": contact.full_name,
        "stale": stale,
        "decayed": decayed,
        "task_created": task_created,
        "trust_score": contact.trust_score,
        "relationship_stage": contact.relationship_stage,
    }


def build_weekly_priority_reason(contact: CommunityContact) -> str:
    if contact.next_follow_up_at and contact.next_follow_up_at <= datetime.utcnow():
        return "Follow-up overdue"
    if is_contact_stale(contact):
        return "Relationship stale"
    if (contact.trust_score or 0) >= 80:
        return "High-trust contact worth maintaining"
    if contact.relationship_stage == "warming":
        return "Warming contact ready for momentum"
    return "General weekly review"


def build_weekly_priority_score(contact: CommunityContact) -> int:
    score = calculate_contact_heat(contact)

    if is_contact_stale(contact):
        score += 10

    if contact.next_follow_up_at and contact.next_follow_up_at <= datetime.utcnow():
        score += 12

    if contact.relationship_stage == "warming":
        score += 5

    return clamp_score(score)


# COMMUNICATION GUARDRAILS & TEMPLATES

QUIET_HOURS_START = 21
QUIET_HOURS_END = 8


def is_quiet_hours(now: datetime | None = None) -> bool:
    now = now or datetime.utcnow()
    hour = now.hour
    if QUIET_HOURS_START <= hour or hour < QUIET_HOURS_END:
        return True
    return False


def resolve_best_channel(contact: CommunityContact) -> str | None:
    if contact.preferred_channel:
        return contact.preferred_channel
    if contact.consent_sms and contact.phone:
        return "sms"
    if contact.consent_email and contact.email:
        return "email"
    if contact.phone:
        return "phone"
    if contact.email:
        return "email"
    return None


def check_contact_channel_allowed(contact: CommunityContact, channel: str) -> tuple[bool, str | None]:
    if channel == "sms":
        if not contact.phone:
            return False, "No phone number on file."
        if not contact.consent_sms:
            return False, "SMS consent not granted."
        if is_quiet_hours():
            return False, "SMS blocked during quiet hours."
        return True, None

    if channel == "email":
        if not contact.email:
            return False, "No email on file."
        if not contact.consent_email:
            return False, "Email consent not granted."
        return True, None

    if channel == "phone":
        if not contact.phone:
            return False, "No phone number on file."
        if is_quiet_hours():
            return False, "Phone contact blocked during quiet hours."
        return True, None

    if channel == "in_person":
        return True, None

    return False, "Unsupported communication channel."


def render_template_text(template, contact: CommunityContact) -> tuple[str | None, str]:
    subject = template.subject
    body = template.body

    replacements = {
        "{{full_name}}": contact.full_name or "",
        "{{first_name}}": (contact.full_name.split(" ")[0] if contact.full_name else ""),
        "{{organization_name}}": contact.organization_name or "",
        "{{region}}": contact.region or "",
        "{{contact_type}}": contact.contact_type or "",
        "{{relationship_stage}}": contact.relationship_stage or "",
    }

    for key, value in replacements.items():
        if subject:
            subject = subject.replace(key, value)
        body = body.replace(key, value)

    return subject, body


def create_blocked_message_log(
    db: Session,
    contact_id: int | None,
    template_id: int | None,
    channel: str,
    subject: str | None,
    body: str,
    reason: str,
    sent_by: str | None = None,
):
    from app.models.community import CommunityMessageLog
    
    row = CommunityMessageLog(
        contact_id=contact_id,
        template_id=template_id,
        channel=channel,
        direction="outbound",
        subject=subject,
        body=body,
        delivery_status="blocked",
        block_reason=reason,
        sent_by=sent_by,
    )
    db.add(row)
    return row


def create_sent_message_log(
    db: Session,
    contact_id: int | None,
    template_id: int | None,
    channel: str,
    subject: str | None,
    body: str,
    sent_by: str | None = None,
    delivery_status: str = "sent",
):
    from app.models.community import CommunityMessageLog
    
    row = CommunityMessageLog(
        contact_id=contact_id,
        template_id=template_id,
        channel=channel,
        direction="outbound",
        subject=subject,
        body=body,
        delivery_status=delivery_status,
        sent_by=sent_by,
        sent_at=datetime.utcnow(),
    )
    db.add(row)
    return row
