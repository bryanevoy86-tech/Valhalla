from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
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
from app.schemas.community import (
    CommunityContactCreate,
    CommunityContactUpdate,
    CommunityContactOut,
    CommunityInteractionCreate,
    CommunityInteractionOut,
    CommunityCampaignCreate,
    CommunityCampaignUpdate,
    CommunityCampaignOut,
    CommunityTaskCreate,
    CommunityTaskUpdate,
    CommunityTaskOut,
    CommunityReferralCreate,
    CommunityReferralOut,
    CommunitySummaryOut,
    CommunityNextActionOut,
    CommunityRegionSummaryOut,
    CommunityAutomationResultOut,
    CommunityWeeklyPriorityOut,
    CommunityTemplateCreate,
    CommunityTemplateUpdate,
    CommunityTemplateOut,
    CommunityMessageLogOut,
    CommunityPreviewMessageOut,
)
from app.services.community_logic import (
    apply_reputation_event,
    score_interaction_effect,
    refresh_contact_stage,
    get_next_best_action,
    calculate_contact_heat,
    process_contact_automation,
    build_weekly_priority_reason,
    build_weekly_priority_score,
    is_contact_stale,
    resolve_best_channel,
    check_contact_channel_allowed,
    render_template_text,
    create_blocked_message_log,
    create_sent_message_log,
)

router = APIRouter(prefix="/api/community", tags=["community"])


# CONTACTS
@router.get("/contacts", response_model=list[CommunityContactOut])
def list_contacts(
    region: str | None = Query(default=None),
    contact_type: str | None = Query(default=None),
    relationship_stage: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(CommunityContact)
    if region:
        q = q.filter(CommunityContact.region == region)
    if contact_type:
        q = q.filter(CommunityContact.contact_type == contact_type)
    if relationship_stage:
        q = q.filter(CommunityContact.relationship_stage == relationship_stage)
    return q.order_by(CommunityContact.full_name.asc()).all()


@router.post("/contacts", response_model=CommunityContactOut)
def create_contact(payload: CommunityContactCreate, db: Session = Depends(get_db)):
    row = CommunityContact(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/contacts/{contact_id}", response_model=CommunityContactOut)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    row = db.query(CommunityContact).filter(CommunityContact.id == contact_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Contact not found")
    return row


@router.patch("/contacts/{contact_id}", response_model=CommunityContactOut)
def update_contact(contact_id: int, payload: CommunityContactUpdate, db: Session = Depends(get_db)):
    row = db.query(CommunityContact).filter(CommunityContact.id == contact_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Contact not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(row, key, value)

    db.commit()
    db.refresh(row)
    return row


# INTERACTIONS
@router.post("/interactions", response_model=CommunityInteractionOut)
def create_interaction(payload: CommunityInteractionCreate, db: Session = Depends(get_db)):
    contact = db.query(CommunityContact).filter(CommunityContact.id == payload.contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    row = CommunityInteraction(**payload.model_dump())
    db.add(row)

    contact.last_contact_at = datetime.utcnow()
    if payload.follow_up_required and payload.follow_up_at:
        contact.next_follow_up_at = payload.follow_up_at

    delta = score_interaction_effect(
        interaction_type=payload.interaction_type,
        outcome=payload.outcome,
        sentiment=payload.sentiment,
    )

    if delta != 0:
        apply_reputation_event(
            db=db,
            contact_id=contact.id,
            event_type="interaction_effect",
            score_delta=delta,
            summary=f"Interaction score adjustment from {payload.interaction_type}/{payload.outcome}/{payload.sentiment}",
        )

    refresh_contact_stage(contact)

    db.commit()
    db.refresh(row)
    return row


@router.get("/interactions", response_model=list[CommunityInteractionOut])
def list_interactions(
    contact_id: int | None = Query(default=None),
    campaign_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(CommunityInteraction)
    if contact_id is not None:
        q = q.filter(CommunityInteraction.contact_id == contact_id)
    if campaign_id is not None:
        q = q.filter(CommunityInteraction.campaign_id == campaign_id)
    return q.order_by(CommunityInteraction.created_at.desc()).all()


@router.get("/contacts/{contact_id}/interactions", response_model=list[CommunityInteractionOut])
def list_contact_interactions(contact_id: int, db: Session = Depends(get_db)):
    return (
        db.query(CommunityInteraction)
        .filter(CommunityInteraction.contact_id == contact_id)
        .order_by(CommunityInteraction.created_at.desc())
        .all()
    )


# CAMPAIGNS
@router.get("/campaigns", response_model=list[CommunityCampaignOut])
def list_campaigns(
    region: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(CommunityCampaign)
    if region:
        q = q.filter(CommunityCampaign.region == region)
    if status:
        q = q.filter(CommunityCampaign.status == status)
    return q.order_by(CommunityCampaign.created_at.desc()).all()


@router.post("/campaigns", response_model=CommunityCampaignOut)
def create_campaign(payload: CommunityCampaignCreate, db: Session = Depends(get_db)):
    row = CommunityCampaign(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/campaigns/{campaign_id}", response_model=CommunityCampaignOut)
def update_campaign(campaign_id: int, payload: CommunityCampaignUpdate, db: Session = Depends(get_db)):
    row = db.query(CommunityCampaign).filter(CommunityCampaign.id == campaign_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Campaign not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(row, key, value)

    db.commit()
    db.refresh(row)
    return row


# TASKS
@router.get("/tasks", response_model=list[CommunityTaskOut])
def list_tasks(
    status: str | None = Query(default=None),
    assigned_to: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(CommunityTask)
    if status:
        q = q.filter(CommunityTask.status == status)
    if assigned_to:
        q = q.filter(CommunityTask.assigned_to == assigned_to)
    return q.order_by(CommunityTask.due_at.asc().nulls_last(), CommunityTask.created_at.desc()).all()


@router.post("/tasks", response_model=CommunityTaskOut)
def create_task(payload: CommunityTaskCreate, db: Session = Depends(get_db)):
    row = CommunityTask(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/tasks/{task_id}", response_model=CommunityTaskOut)
def update_task(task_id: int, payload: CommunityTaskUpdate, db: Session = Depends(get_db)):
    row = db.query(CommunityTask).filter(CommunityTask.id == task_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(row, key, value)

    if row.status == "done" and row.completed_at is None:
        row.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(row)
    return row


# REFERRALS
@router.post("/referrals", response_model=CommunityReferralOut)
def create_referral(payload: CommunityReferralCreate, db: Session = Depends(get_db)):
    row = CommunityReferral(**payload.model_dump())
    db.add(row)

    if payload.source_contact_id:
        apply_reputation_event(
            db=db,
            contact_id=payload.source_contact_id,
            event_type="referral_created",
            score_delta=6,
            summary=f"Referral created for type: {payload.referral_type}",
        )
        source_contact = db.query(CommunityContact).filter(CommunityContact.id == payload.source_contact_id).first()
        if source_contact:
            refresh_contact_stage(source_contact)

    db.commit()
    db.refresh(row)
    return row


@router.get("/referrals", response_model=list[CommunityReferralOut])
def list_referrals(db: Session = Depends(get_db)):
    return db.query(CommunityReferral).order_by(CommunityReferral.created_at.desc()).all()


# SUMMARY
@router.get("/summary", response_model=CommunitySummaryOut)
def get_summary(db: Session = Depends(get_db)):
    now = datetime.utcnow()

    total_contacts = db.query(func.count(CommunityContact.id)).scalar() or 0
    active_contacts = (
        db.query(func.count(CommunityContact.id))
        .filter(CommunityContact.relationship_stage.in_(["warming", "active", "trusted"]))
        .scalar()
        or 0
    )
    follow_ups_due = (
        db.query(func.count(CommunityContact.id))
        .filter(CommunityContact.next_follow_up_at.isnot(None))
        .filter(CommunityContact.next_follow_up_at <= now)
        .scalar()
        or 0
    )
    open_tasks = (
        db.query(func.count(CommunityTask.id))
        .filter(CommunityTask.status.in_(["open", "in_progress"]))
        .scalar()
        or 0
    )
    active_campaigns = (
        db.query(func.count(CommunityCampaign.id))
        .filter(CommunityCampaign.status == "active")
        .scalar()
        or 0
    )
    total_referrals = db.query(func.count(CommunityReferral.id)).scalar() or 0
    hot_contacts = (
        db.query(func.count(CommunityContact.id))
        .filter(CommunityContact.trust_score >= 80)
        .scalar()
        or 0
    )

    return CommunitySummaryOut(
        total_contacts=total_contacts,
        active_contacts=active_contacts,
        follow_ups_due=follow_ups_due,
        open_tasks=open_tasks,
        active_campaigns=active_campaigns,
        total_referrals=total_referrals,
        hot_contacts=hot_contacts,
    )


# TRUST ADJUSTMENT
@router.post("/contacts/{contact_id}/adjust-trust", response_model=CommunityContactOut)
def adjust_contact_trust(
    contact_id: int,
    score_delta: int = Query(..., ge=-100, le=100),
    reason: str = Query(..., min_length=3),
    db: Session = Depends(get_db),
):
    contact = db.query(CommunityContact).filter(CommunityContact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    apply_reputation_event(
        db=db,
        contact_id=contact.id,
        event_type="manual_adjustment",
        score_delta=score_delta,
        summary=reason,
    )

    refresh_contact_stage(contact)

    db.commit()
    db.refresh(contact)
    return contact


# NEXT-BEST-ACTION
@router.get("/contacts/{contact_id}/next-action", response_model=CommunityNextActionOut)
def contact_next_action(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(CommunityContact).filter(CommunityContact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    decision = get_next_best_action(contact)
    heat = calculate_contact_heat(contact)

    return CommunityNextActionOut(
        contact_id=contact.id,
        full_name=contact.full_name,
        relationship_stage=contact.relationship_stage,
        trust_score=contact.trust_score,
        heat_score=heat,
        action=decision["action"],
        priority=decision["priority"],
        reason=decision["reason"],
    )


# HOTTEST CONTACTS
@router.get("/hottest-contacts", response_model=list[CommunityNextActionOut])
def hottest_contacts(limit: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db)):
    contacts = db.query(CommunityContact).all()

    ranked = []
    for contact in contacts:
        decision = get_next_best_action(contact)
        heat = calculate_contact_heat(contact)
        ranked.append(
            CommunityNextActionOut(
                contact_id=contact.id,
                full_name=contact.full_name,
                relationship_stage=contact.relationship_stage,
                trust_score=contact.trust_score,
                heat_score=heat,
                action=decision["action"],
                priority=decision["priority"],
                reason=decision["reason"],
            )
        )

    ranked.sort(key=lambda x: x.heat_score, reverse=True)
    return ranked[:limit]


# REGION SUMMARY
@router.get("/regions/{region}/summary", response_model=CommunityRegionSummaryOut)
def region_summary(region: str, db: Session = Depends(get_db)):
    now = datetime.utcnow()

    total_contacts = (
        db.query(func.count(CommunityContact.id))
        .filter(CommunityContact.region == region)
        .scalar()
        or 0
    )

    trusted_contacts = (
        db.query(func.count(CommunityContact.id))
        .filter(CommunityContact.region == region, CommunityContact.relationship_stage == "trusted")
        .scalar()
        or 0
    )

    active_contacts = (
        db.query(func.count(CommunityContact.id))
        .filter(CommunityContact.region == region, CommunityContact.relationship_stage == "active")
        .scalar()
        or 0
    )

    warming_contacts = (
        db.query(func.count(CommunityContact.id))
        .filter(CommunityContact.region == region, CommunityContact.relationship_stage == "warming")
        .scalar()
        or 0
    )

    new_contacts = (
        db.query(func.count(CommunityContact.id))
        .filter(CommunityContact.region == region, CommunityContact.relationship_stage == "new")
        .scalar()
        or 0
    )

    follow_ups_due = (
        db.query(func.count(CommunityContact.id))
        .filter(CommunityContact.region == region)
        .filter(CommunityContact.next_follow_up_at.isnot(None))
        .filter(CommunityContact.next_follow_up_at <= now)
        .scalar()
        or 0
    )

    open_tasks = (
        db.query(func.count(CommunityTask.id))
        .join(CommunityContact, CommunityTask.contact_id == CommunityContact.id, isouter=True)
        .filter(CommunityContact.region == region)
        .filter(CommunityTask.status.in_(["open", "in_progress"]))
        .scalar()
        or 0
    )

    total_referrals = (
        db.query(func.count(CommunityReferral.id))
        .join(CommunityContact, CommunityReferral.source_contact_id == CommunityContact.id, isouter=True)
        .filter(CommunityContact.region == region)
        .scalar()
        or 0
    )

    return CommunityRegionSummaryOut(
        region=region,
        total_contacts=total_contacts,
        trusted_contacts=trusted_contacts,
        active_contacts=active_contacts,
        warming_contacts=warming_contacts,
        new_contacts=new_contacts,
        follow_ups_due=follow_ups_due,
        open_tasks=open_tasks,
        total_referrals=total_referrals,
    )


# REPUTATION LOG
@router.get("/contacts/{contact_id}/reputation-events")
def contact_reputation_events(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(CommunityContact).filter(CommunityContact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    rows = (
        db.query(CommunityReputationEvent)
        .filter(CommunityReputationEvent.contact_id == contact_id)
        .order_by(CommunityReputationEvent.created_at.desc())
        .all()
    )

    return [
        {
            "id": row.id,
            "event_type": row.event_type,
            "score_delta": row.score_delta,
            "summary": row.summary,
            "created_at": row.created_at,
        }
        for row in rows
    ]


# STALE RELATIONSHIP DETECTION
@router.get("/stale-contacts", response_model=list[CommunityContactOut])
def stale_contacts(db: Session = Depends(get_db)):
    contacts = db.query(CommunityContact).all()
    stale = [c for c in contacts if is_contact_stale(c)]
    stale.sort(key=lambda x: (x.next_follow_up_at or datetime.min, x.full_name))
    return stale


# AUTOMATION ENGINE
@router.post("/automation/run", response_model=list[CommunityAutomationResultOut])
def run_community_automation(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    contacts = (
        db.query(CommunityContact)
        .order_by(CommunityContact.updated_at.asc())
        .limit(limit)
        .all()
    )

    results = []
    for contact in contacts:
        result = process_contact_automation(db, contact)
        results.append(CommunityAutomationResultOut(**result))

    db.commit()

    return results


@router.post("/contacts/{contact_id}/automation", response_model=CommunityAutomationResultOut)
def run_contact_automation(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(CommunityContact).filter(CommunityContact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    result = process_contact_automation(db, contact)
    db.commit()

    return CommunityAutomationResultOut(**result)


# WEEKLY PRIORITY QUEUE
@router.get("/weekly-priority-queue", response_model=list[CommunityWeeklyPriorityOut])
def weekly_priority_queue(
    region: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(CommunityContact)
    if region:
        q = q.filter(CommunityContact.region == region)

    contacts = q.all()

    ranked = []
    for contact in contacts:
        decision = get_next_best_action(contact)
        heat = calculate_contact_heat(contact)
        weekly_score = build_weekly_priority_score(contact)
        reason = build_weekly_priority_reason(contact)

        ranked.append(
            CommunityWeeklyPriorityOut(
                contact_id=contact.id,
                full_name=contact.full_name,
                region=contact.region,
                relationship_stage=contact.relationship_stage,
                trust_score=contact.trust_score,
                heat_score=heat,
                weekly_priority_score=weekly_score,
                reason=reason,
                next_action=decision["action"],
                priority=decision["priority"],
            )
        )

    ranked.sort(key=lambda x: x.weekly_priority_score, reverse=True)
    return ranked[:limit]


# OVERDUE FOLLOW-UPS
@router.get("/overdue-follow-ups", response_model=list[CommunityTaskOut])
def overdue_follow_ups(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    rows = (
        db.query(CommunityTask)
        .filter(CommunityTask.task_type == "follow_up")
        .filter(CommunityTask.status.in_(["open", "in_progress"]))
        .filter(CommunityTask.due_at.isnot(None))
        .filter(CommunityTask.due_at <= now)
        .order_by(CommunityTask.due_at.asc())
        .all()
    )
    return rows


# SCHEDULE FOLLOW-UP
@router.post("/contacts/{contact_id}/schedule-follow-up", response_model=CommunityTaskOut)
def schedule_follow_up_now(
    contact_id: int,
    due_in_days: int = Query(default=1, ge=0, le=30),
    priority: str = Query(default="high"),
    db: Session = Depends(get_db),
):
    contact = db.query(CommunityContact).filter(CommunityContact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    existing = (
        db.query(CommunityTask)
        .filter(CommunityTask.contact_id == contact_id)
        .filter(CommunityTask.task_type == "follow_up")
        .filter(CommunityTask.status.in_(["open", "in_progress"]))
        .first()
    )
    if existing:
        return existing

    task = CommunityTask(
        contact_id=contact.id,
        task_type="follow_up",
        title=f"Follow up with {contact.full_name}",
        description="Manual follow-up task created from community module.",
        due_at=datetime.utcnow() + timedelta(days=due_in_days),
        priority=priority,
        status="open",
        assigned_to=contact.owner_user_id or "operator",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# TEMPLATES
@router.get("/templates", response_model=list[CommunityTemplateOut])
def list_templates(
    channel: str | None = Query(default=None),
    template_type: str | None = Query(default=None),
    audience_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(CommunityTemplate)
    if channel:
        q = q.filter(CommunityTemplate.channel == channel)
    if template_type:
        q = q.filter(CommunityTemplate.template_type == template_type)
    if audience_type:
        q = q.filter(CommunityTemplate.audience_type == audience_type)
    if status:
        q = q.filter(CommunityTemplate.status == status)
    return q.order_by(CommunityTemplate.name.asc()).all()


@router.post("/templates", response_model=CommunityTemplateOut)
def create_template(payload: CommunityTemplateCreate, db: Session = Depends(get_db)):
    row = CommunityTemplate(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/templates/{template_id}", response_model=CommunityTemplateOut)
def update_template(template_id: int, payload: CommunityTemplateUpdate, db: Session = Depends(get_db)):
    row = db.query(CommunityTemplate).filter(CommunityTemplate.id == template_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Template not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(row, key, value)

    db.commit()
    db.refresh(row)
    return row


# MESSAGE PREVIEW
@router.get("/contacts/{contact_id}/preview-message", response_model=CommunityPreviewMessageOut)
def preview_message(
    contact_id: int,
    template_id: int = Query(...),
    db: Session = Depends(get_db),
):
    contact = db.query(CommunityContact).filter(CommunityContact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    template = db.query(CommunityTemplate).filter(CommunityTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    best_channel = resolve_best_channel(contact)
    subject, body = render_template_text(template, contact)
    allowed, reason = check_contact_channel_allowed(contact, template.channel)

    return CommunityPreviewMessageOut(
        contact_id=contact.id,
        full_name=contact.full_name,
        channel=template.channel,
        allowed=allowed,
        best_channel=best_channel,
        block_reason=reason,
        subject=subject,
        body=body,
    )


# SEND MESSAGE WITH GUARDRAILS
@router.post("/contacts/{contact_id}/send-template", response_model=CommunityMessageLogOut)
def send_template_to_contact(
    contact_id: int,
    template_id: int = Query(...),
    sent_by: str = Query(default="operator"),
    db: Session = Depends(get_db),
):
    contact = db.query(CommunityContact).filter(CommunityContact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    template = db.query(CommunityTemplate).filter(CommunityTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.status != "approved" or template.approval_status != "approved":
        raise HTTPException(status_code=400, detail="Template is not approved for sending")

    subject, body = render_template_text(template, contact)
    allowed, reason = check_contact_channel_allowed(contact, template.channel)

    if not allowed:
        row = create_blocked_message_log(
            db=db,
            contact_id=contact.id,
            template_id=template.id,
            channel=template.channel,
            subject=subject,
            body=body,
            reason=reason or "Blocked by communication guardrails.",
            sent_by=sent_by,
        )
        db.commit()
        db.refresh(row)
        return row

    row = create_sent_message_log(
        db=db,
        contact_id=contact.id,
        template_id=template.id,
        channel=template.channel,
        subject=subject,
        body=body,
        sent_by=sent_by,
        delivery_status="sent",
    )

    interaction = CommunityInteraction(
        contact_id=contact.id,
        interaction_type=template.channel,
        direction="outbound",
        subject=subject,
        summary=body,
        outcome="sent_template",
        sentiment="neutral",
        follow_up_required=False,
        performed_by=sent_by,
    )
    db.add(interaction)

    contact.last_contact_at = datetime.utcnow()

    db.commit()
    db.refresh(row)
    return row


# MESSAGE LOGS
@router.get("/message-logs", response_model=list[CommunityMessageLogOut])
def list_message_logs(
    contact_id: int | None = Query(default=None),
    channel: str | None = Query(default=None),
    delivery_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(CommunityMessageLog)
    if contact_id is not None:
        q = q.filter(CommunityMessageLog.contact_id == contact_id)
    if channel:
        q = q.filter(CommunityMessageLog.channel == channel)
    if delivery_status:
        q = q.filter(CommunityMessageLog.delivery_status == delivery_status)
    return q.order_by(CommunityMessageLog.created_at.desc()).all()
