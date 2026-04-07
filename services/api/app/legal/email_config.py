from __future__ import annotations

import os


def get_legal_email_config() -> dict:
    return {
        "sender_email": os.getenv("LEGAL_SENDER_EMAIL", "").strip(),
        "smtp_host": os.getenv("LEGAL_SMTP_HOST", "").strip(),
        "smtp_port": int(os.getenv("LEGAL_SMTP_PORT", "587")),
        "smtp_username": os.getenv("LEGAL_SMTP_USERNAME", "").strip(),
        "smtp_password": os.getenv("LEGAL_SMTP_PASSWORD", "").strip(),
        "use_tls": os.getenv("LEGAL_SMTP_USE_TLS", "true").strip().lower() in ("1", "true", "yes", "on"),
    }


def legal_email_config_ready() -> tuple[bool, list[str]]:
    cfg = get_legal_email_config()
    missing = [k for k, v in cfg.items() if k != "smtp_port" and v in ("", None)]
    return (len(missing) == 0, missing)
