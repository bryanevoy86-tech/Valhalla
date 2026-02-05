"""Alerts system - send notifications for important events."""
from datetime import datetime
from app.core.runtime_flags import is_live


def send_alert(alert_type: str, message: str, severity: str = "info") -> dict:
    """
    Send an alert.
    
    Args:
        alert_type: Type of alert (deal_approved, offer_sent, signature_complete, etc)
        message: Alert message
        severity: info, warning, critical
    
    Returns:
        dict with alert details
    """
    alert = {
        "alert_id": f"alert_{datetime.utcnow().timestamp()}",
        "type": alert_type,
        "message": message,
        "severity": severity,
        "timestamp": datetime.utcnow().isoformat(),
        "mode": "live" if is_live() else "sandbox"
    }
    
    # In real implementation, would send via email/SMS/webhook
    return alert


def send_daily_summary_alert(summary: dict) -> dict:
    """Send daily summary as alert."""
    message = f"""
    Daily Summary:
    - Deals: {summary.get('deals_processed')}
    - Offers: {summary.get('offers_sent')}
    - Contracts: {summary.get('contracts_signed')}
    - Revenue: ${summary.get('revenue_recorded', 0):,.2f}
    """
    
    return send_alert(
        alert_type="daily_summary",
        message=message.strip(),
        severity="info"
    )


def send_critical_alert(message: str) -> dict:
    """Send critical alert."""
    return send_alert(
        alert_type="critical_event",
        message=message,
        severity="critical"
    )
