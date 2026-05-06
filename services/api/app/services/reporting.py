"""Reporting and analytics services for VA Intake system."""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import VALead, VAApprovalQueue, VAAuditLog


def get_va_leads_summary(db: Session) -> dict:
    """
    Get summary statistics for VA leads.
    
    Args:
        db: Database session
    
    Returns:
        dict with lead statistics
    """
    
    all_leads = db.query(VALead).all()
    total_leads = len(all_leads)
    
    # Count by status
    status_counts = {}
    for lead in all_leads:
        status = lead.status or "unknown"
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Count by stage
    stage_counts = {}
    for lead in all_leads:
        stage = lead.stage or "unknown"
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
    
    # Average score
    scores = [l.heimdall_score for l in all_leads if l.heimdall_score]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    # Total value
    total_value = sum(l.asking_price or 0 for l in all_leads)
    
    # Leads by source
    source_counts = {}
    for lead in all_leads:
        source = lead.source_platform or "unknown"
        source_counts[source] = source_counts.get(source, 0) + 1
    
    # Leads created today/this week/this month
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)
    
    leads_today = 0
    leads_this_week = 0
    leads_this_month = 0
    
    for l in all_leads:
        if not l.created_at:
            continue
        
        # Make created_at timezone-aware if needed
        created = l.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        
        if created >= today_start:
            leads_today += 1
        if created >= week_start:
            leads_this_week += 1
        if created >= month_start:
            leads_this_month += 1
    
    return {
        "success": True,
        "report_type": "va_leads_summary",
        "generated_at": now.isoformat(),
        "totals": {
            "total_leads": total_leads,
            "total_property_value": total_value,
            "average_heimdall_score": round(avg_score, 1),
        },
        "by_status": status_counts,
        "by_stage": stage_counts,
        "by_source": source_counts,
        "activity": {
            "leads_today": leads_today,
            "leads_this_week": leads_this_week,
            "leads_this_month": leads_this_month,
        },
        "quality": {
            "high_quality": sum(1 for l in all_leads if l.heimdall_score >= 75),
            "medium_quality": sum(1 for l in all_leads if 55 <= l.heimdall_score < 75),
            "low_quality": sum(1 for l in all_leads if l.heimdall_score < 55),
        }
    }


def get_approval_summary(db: Session) -> dict:
    """
    Get summary of approval workflow metrics.
    
    Args:
        db: Database session
    
    Returns:
        dict with approval statistics
    """
    
    all_approvals = db.query(VAApprovalQueue).all()
    total_approvals = len(all_approvals)
    
    # Count by status
    status_counts = {
        "pending": sum(1 for a in all_approvals if a.status == "pending"),
        "approved": sum(1 for a in all_approvals if a.status == "approved"),
        "denied": sum(1 for a in all_approvals if a.status == "denied"),
        "cancelled": sum(1 for a in all_approvals if a.status == "cancelled"),
    }
    
    # Average time to approval
    pending = [a for a in all_approvals if a.status == "pending"]
    approved = [a for a in all_approvals if a.status == "approved"]
    
    avg_approval_time_hours = None
    if approved:
        times = []
        for a in approved:
            if a.created_at and a.approved_at:
                # Handle timezone-naive datetimes
                created = a.created_at
                approved_at = a.approved_at
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                if approved_at.tzinfo is None:
                    approved_at = approved_at.replace(tzinfo=timezone.utc)
                
                delta = approved_at - created
                times.append(delta.total_seconds() / 3600)  # to hours
        if times:
            avg_approval_time_hours = round(sum(times) / len(times), 1)
    
    # Approval rate
    approval_rate = (status_counts["approved"] / total_approvals * 100) if total_approvals > 0 else 0
    
    # Risk distribution of pending
    pending_risk = {}
    for a in pending:
        risk = a.risk_level or "unknown"
        pending_risk[risk] = pending_risk.get(risk, 0) + 1
    
    return {
        "success": True,
        "report_type": "approval_summary",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "totals": {
            "total_in_queue": total_approvals,
            "pending": status_counts["pending"],
            "approved": status_counts["approved"],
            "denied": status_counts["denied"],
        },
        "metrics": {
            "approval_rate_percent": round(approval_rate, 1),
            "average_approval_time_hours": avg_approval_time_hours,
            "denial_rate_percent": round((status_counts["denied"] / total_approvals * 100) if total_approvals > 0 else 0, 1),
        },
        "pending_risk_distribution": pending_risk,
        "next_action": f"Review {status_counts['pending']} pending approvals" if status_counts["pending"] > 0 else "No pending approvals"
    }


def get_eia_monthly_summary(db: Session, year: int = None, month: int = None) -> dict:
    """
    Get EIA (Economic Impact Assessment) monthly summary.
    
    This helps track activity for reporting periods.
    
    Args:
        db: Database session
        year: Year (defaults to current)
        month: Month (defaults to current)
    
    Returns:
        dict with monthly activity summary
    """
    
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month
    
    # Date range for the month
    month_start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        month_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
    else:
        month_end = datetime(year, month + 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
    
    # Get leads created this month
    all_leads = db.query(VALead).all()
    leads_this_month = []
    
    for lead in all_leads:
        if not lead.created_at:
            continue
        
        created = lead.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        
        if month_start <= created <= month_end:
            leads_this_month.append(lead)
    
    # Get approvals this month
    all_approvals = db.query(VAApprovalQueue).all()
    approvals_this_month = []
    
    for approval in all_approvals:
        if not approval.created_at:
            continue
        
        created = approval.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        
        if month_start <= created <= month_end:
            approvals_this_month.append(approval)
    
    # Get conversions this month
    conversions = [l for l in leads_this_month if l.deal_id]
    
    # Calculate metrics
    total_leads = len(leads_this_month)
    total_value = sum(l.asking_price or 0 for l in leads_this_month)
    avg_value = total_value / total_leads if total_leads > 0 else 0
    
    approved_count = sum(1 for a in approvals_this_month if a.status == "approved")
    approval_rate = (approved_count / len(approvals_this_month) * 100) if approvals_this_month else 0
    
    conversion_count = len(conversions)
    conversion_rate = (conversion_count / total_leads * 100) if total_leads > 0 else 0
    
    return {
        "success": True,
        "report_type": "eia_monthly_summary",
        "period": f"{year}-{month:02d}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "intake_activity": {
            "leads_submitted": total_leads,
            "total_property_value": round(total_value, 2),
            "average_property_value": round(avg_value, 2),
            "sources": {}
        },
        "approval_activity": {
            "total_in_queue": len(approvals_this_month),
            "approved": approved_count,
            "denied": sum(1 for a in approvals_this_month if a.status == "denied"),
            "approval_rate_percent": round(approval_rate, 1),
        },
        "conversion_activity": {
            "leads_converted_to_deals": conversion_count,
            "conversion_rate_percent": round(conversion_rate, 1),
            "total_deal_value": round(sum(l.asking_price or 0 for l in conversions), 2),
        },
        "quality_metrics": {
            "average_heimdall_score": round(sum(l.heimdall_score or 0 for l in leads_this_month) / total_leads, 1) if total_leads > 0 else 0,
            "high_quality_leads": sum(1 for l in leads_this_month if l.heimdall_score >= 75),
        },
        "efficiency": {
            "leads_per_day": round(total_leads / 30, 1),
            "approval_efficiency": f"{approved_count} approved from {len(approvals_this_month)} reviewed",
        }
    }
