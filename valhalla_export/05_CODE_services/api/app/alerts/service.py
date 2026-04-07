from typing import List
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText

from app.metrics.schemas import MetricsOut
from .schemas import AlertOut, AlertResponseOut


class AlertsService:
    """Check metrics against thresholds and generate alerts."""

    @staticmethod
    def check_thresholds(metrics: MetricsOut) -> List[AlertOut]:
        """
        Compare metrics to thresholds and return alerts if exceeded.
        
        Thresholds:
        - error_rate > 0.1 (10%)
        - p50_latency > 1.0 (seconds)
        """
        alerts = []
        now = datetime.utcnow().isoformat()

        if metrics.error_rate is not None and metrics.error_rate > 0.1:
            alerts.append(
                AlertOut(
                    alert_type="error_rate_high",
                    message=f"Error rate exceeded 10% threshold: {metrics.error_rate:.2%}",
                    triggered_at=now,
                )
            )

        if metrics.p50_latency is not None and metrics.p50_latency > 1.0:
            alerts.append(
                AlertOut(
                    alert_type="high_latency",
                    message=f"p50 latency exceeded 1.0s threshold: {metrics.p50_latency:.3f}s",
                    triggered_at=now,
                )
            )

        return alerts

    @staticmethod
    def handle_alert(alert: AlertOut) -> AlertResponseOut:
        """Trigger an action in response to an alert.

        Currently supports sending an email when high latency occurs.
        """
        now = datetime.utcnow().isoformat()

        # Example: handle high latency with an email notification
        if alert.alert_type == "high_latency":
            ok, info = AlertsService.send_email_notification(alert)
            return AlertResponseOut(
                action_type="email_notification",
                message=info,
                triggered_at=now,
                status="success" if ok else "failed",
            )

        # Default no-op for other alert types (extensible)
        return AlertResponseOut(
            action_type="noop",
            message=f"No handler configured for alert_type='{alert.alert_type}'",
            triggered_at=now,
            status="ignored",
        )

    @staticmethod
    def send_email_notification(alert: AlertOut) -> tuple[bool, str]:
        """Send an email notification for the given alert.

        Returns (ok, message). Uses env vars if provided, else a safe no-op.
        """
        from_email = os.getenv("ALERTS_FROM_EMAIL", "noreply@example.com")
        to_email = os.getenv("ALERTS_TO_EMAIL", "admin@example.com")
        smtp_host = os.getenv("ALERTS_SMTP_HOST", "smtp.example.com")
        smtp_port = int(os.getenv("ALERTS_SMTP_PORT", "25"))

        subject = f"Valhalla Alert: {alert.alert_type}"
        body = f"{alert.message}\nTriggered at: {alert.triggered_at}"
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email

        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=5) as server:
                server.sendmail(from_email, [to_email], msg.as_string())
            return True, f"Email notification sent to {to_email}"
        except Exception as e:
            return False, f"Email send failed: {e}"
