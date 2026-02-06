"""
Module 63: Alert Router
REST endpoints for alert management.
"""
from fastapi import APIRouter, Request
from app.alerts.engine import send_alert, send_batch_alerts, get_alert_history

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/send")
async def send_alert_endpoint(request: Request):
    """
    Send an alert.
    
    Request body:
        {
            "message": "Alert message",
            "severity": "info",
            "recipient": "user@example.com",
            "channel": "email"
        }
    """
    try:
        data = await request.json()
        message = data.get("message")
        severity = data.get("severity", "info")
        recipient = data.get("recipient")
        channel = data.get("channel", "email")
        
        result = send_alert(
            message=message,
            severity=severity,
            recipient=recipient,
            channel=channel
        )
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/batch")
async def send_batch(request: Request):
    """
    Send batch of alerts.
    
    Request body:
        {
            "alerts": [
                {"message": "...", "severity": "..."},
                ...
            ]
        }
    """
    try:
        data = await request.json()
        alerts = data.get("alerts", [])
        
        result = send_batch_alerts(alerts)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/history")
def get_history(limit: int = 10, severity: str = None):
    """
    Get alert history.
    
    Args:
        limit: Max alerts to return
        severity: Filter by severity
    """
    result = get_alert_history(limit=limit, severity=severity)
    return {
        "status": "success",
        "data": result
    }
