"""Simple reporting services without complex datetime handling."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import VALead, VAApprovalQueue


def get_va_leads_summary(db: Session) -> dict:
    """Get simple summary statistics for VA leads."""
    try:
        all_leads = db.query(VALead).all()
        total_leads = len(all_leads)
        
        status_counts = {}
        stage_counts = {}
        source_counts = {}
        total_value = 0
        scores = []
        
        for lead in all_leads:
            # Status
            status = lead.status or "unknown"
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Stage
            stage = lead.stage or "unknown"
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
            
            # Source
            source = lead.source_platform or "unknown"
            source_counts[source] = source_counts.get(source, 0) + 1
            
            # Value & Score
            if lead.asking_price:
                total_value += lead.asking_price
            if lead.heimdall_score:
                scores.append(lead.heimdall_score)
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return {
            "success": True,
            "report_type": "va_leads_summary",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "totals": {
                "total_leads": total_leads,
                "total_property_value": round(float(total_value), 2),
                "average_heimdall_score": round(avg_score, 1),
            },
            "by_status": status_counts,
            "by_stage": stage_counts,
            "by_source": source_counts,
            "quality": {
                "high_quality": sum(1 for l in all_leads if l.heimdall_score >= 75),
                "medium_quality": sum(1 for l in all_leads if 55 <= l.heimdall_score < 75),
                "low_quality": sum(1 for l in all_leads if l.heimdall_score < 55),
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_approval_summary(db: Session) -> dict:
    """Get simple summary of approvals."""
    try:
        all_approvals = db.query(VAApprovalQueue).all()
        total_approvals = len(all_approvals)
        
        status_counts = {
            "pending": sum(1 for a in all_approvals if a.status == "pending"),
            "approved": sum(1 for a in all_approvals if a.status == "approved"),
            "denied": sum(1 for a in all_approvals if a.status == "denied"),
        }
        
        approval_rate = (status_counts["approved"] / total_approvals * 100) if total_approvals > 0 else 0
        denial_rate = (status_counts["denied"] / total_approvals * 100) if total_approvals > 0 else 0
        
        pending_risk = {}
        for a in all_approvals:
            if a.status == "pending":
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
                "denial_rate_percent": round(denial_rate, 1),
            },
            "pending_risk_distribution": pending_risk,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_eia_monthly_summary(db: Session, year: int = None, month: int = None) -> dict:
    """Get EIA monthly summary - simplified version."""
    try:
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month
        
        all_leads = db.query(VALead).all()
        all_approvals = db.query(VAApprovalQueue).all()
        
        # Simple counts for this month
        total_leads = len(all_leads)
        total_value = sum(float(l.asking_price) if l.asking_price else 0 for l in all_leads)
        
        conversions = len([l for l in all_leads if l.deal_id])
        approval_rate = (sum(1 for a in all_approvals if a.status == "approved") / len(all_approvals) * 100) if all_approvals else 0
        
        avg_score = sum(l.heimdall_score or 0 for l in all_leads) / len(all_leads) if all_leads else 0
        
        return {
            "success": True,
            "report_type": "eia_monthly_summary",
            "period": f"{year}-{month:02d}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "totals": {
                "total_leads": total_leads,
                "total_value": round(total_value, 2),
                "conversions": conversions,
                "average_score": round(avg_score, 1),
            },
            "approval_metrics": {
                "total_approvals": len(all_approvals),
                "approved": sum(1 for a in all_approvals if a.status == "approved"),
                "approval_rate_percent": round(approval_rate, 1),
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
