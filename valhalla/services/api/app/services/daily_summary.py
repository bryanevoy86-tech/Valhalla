"""
Daily Summary Service

Provides functions for building and sending daily system summaries.
Uses the system email identity as the default recipient.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.identity import get_system_email, system_identity
from app.services.email_service import send_summary as send_summary_email


def get_default_summary_recipient() -> str:
    """
    Get the default recipient for daily system summaries.

    Returns the system email address configured in VALHALLA_SYSTEM_EMAIL.

    Returns:
        str: The system email address

    Raises:
        RuntimeError: If VALHALLA_SYSTEM_EMAIL is not configured
    """
    return get_system_email()


def send_daily_summary(
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    to_email: Optional[str] = None,
) -> bool:
    """
    Send a daily system summary email.

    Uses the system email identity as sender and defaults to system email
    as recipient if not specified.

    Args:
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML email body
        to_email: Recipient email. Defaults to system email.

    Returns:
        bool: True if sent successfully, False otherwise
    """
    if to_email is None:
        to_email = get_default_summary_recipient()

    return send_summary_email(
        subject=subject,
        body=body,
        html_body=html_body,
        to_email=to_email,
    )


def format_summary_report(
    title: str,
    sections: Dict[str, str],
    footer: Optional[str] = None,
) -> str:
    """
    Format a summary report with sections.

    Args:
        title: Report title
        sections: Dict of section_name -> section_content
        footer: Optional footer text

    Returns:
        str: Formatted plain text report
    """
    lines = [
        f"{'=' * 60}",
        f"  {title}",
        f"  {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"{'=' * 60}",
        "",
    ]

    for section_name, section_content in sections.items():
        lines.append(f"--- {section_name} ---")
        lines.append(section_content)
        lines.append("")

    if footer:
        lines.append("")
        lines.append(footer)

    return "\n".join(lines)


def format_summary_html(
    title: str,
    sections: Dict[str, str],
    footer: Optional[str] = None,
) -> str:
    """
    Format a summary report as HTML.

    Args:
        title: Report title
        sections: Dict of section_name -> section_content (can be HTML)
        footer: Optional footer text

    Returns:
        str: Formatted HTML report
    """
    identity = system_identity()
    from_name = identity["from_name"]

    sections_html = ""
    for section_name, section_content in sections.items():
        sections_html += f"""
        <div style="margin-bottom: 20px;">
            <h3 style="color: #333; border-bottom: 1px solid #ddd; padding-bottom: 5px;">
                {section_name}
            </h3>
            <pre style="background: #f5f5f5; padding: 10px; overflow-x: auto;">
{section_content}
            </pre>
        </div>
        """

    footer_html = ""
    if footer:
        footer_html = f"""
        <hr style="border: 0; border-top: 1px solid #ddd; margin-top: 20px;">
        <p style="font-size: 12px; color: #666;">
            {footer}
        </p>
        """

    return f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #222; border-bottom: 3px solid #0066cc; padding-bottom: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{title}</h1>
                <p style="font-size: 12px; color: #999;">
                    Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
                </p>
                {sections_html}
                {footer_html}
                <p style="font-size: 11px; color: #999; margin-top: 30px;">
                    This is an automated message from {from_name}.
                </p>
            </div>
        </body>
    </html>
    """
