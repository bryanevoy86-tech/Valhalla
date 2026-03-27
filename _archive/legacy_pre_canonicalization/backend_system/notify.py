# --- Discord webhook notifier (CH83) ---
import json
import logging
import os
import urllib.request

log = logging.getLogger("notify")


def _discord_url() -> str | None:
    return os.getenv("DISCORD_WEBHOOK_URL") or None


def post_discord(text: str, embeds: list | None = None) -> bool:
    url = _discord_url()
    if not url:
        log.info("[notify] %s", text)
        return False
    payload = {"content": text}
    if embeds:
        payload["embeds"] = embeds
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=6) as _:
            pass
        return True
    except Exception as e:
        log.warning("discord webhook failed: %s", e)
        return False


from __future__ import annotations

import re
import smtplib
import socket
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

APP_ROOT = Path(".").resolve()


def _cfg_get(cfg: Dict[str, Any], path: List[str], default=None):
    cur = cfg
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def _collect_secret_values(cfg: Dict[str, Any]) -> List[str]:
    names = _cfg_get(cfg, ["notify", "redact", "keys_env"], []) or []
    vals = []
    for n in names:
        v = os.getenv(n)
        if v:
            vals.append(v)
    return vals


def _redactor(cfg: Dict[str, Any]):
    pats = _cfg_get(cfg, ["notify", "redact", "patterns"], []) or []
    regs = [re.compile(p) for p in pats if p]
    secrets = _collect_secret_values(cfg)
    max_bytes = int(_cfg_get(cfg, ["notify", "redact", "max_tail_bytes"], 4000) or 4000)

    def redact_text(t: str) -> str:
        if t is None:
            return ""
        out = t
        for r in regs:
            out = r.sub("[redacted]", out)
        for s in secrets:
            if s:
                out = out.replace(s, "[redacted]")
        if len(out.encode("utf-8")) > max_bytes:
            # keep tail (most recent output)
            b = out.encode("utf-8")
            out = b[-max_bytes:].decode("utf-8", errors="ignore")
            out = "[truncated]\n" + out
        return out

    def redact_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        try:
            s = json.dumps(d, ensure_ascii=False, default=str)
            s2 = redact_text(s)
            return json.loads(s2)
        except Exception:
            return d

    return redact_text, redact_dict


async def _send_webhook(url: str, kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    timeout = httpx.Timeout(10.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        if kind == "discord":
            # Discord expects {"content": "..."} (embeds optional)
            content = payload.get("text") or json.dumps(payload, ensure_ascii=False)
            data = {"content": content[:1990]}  # safety limit
            r = await client.post(url, json=data)
        else:
            r = await client.post(url, json=payload)
        return {"status": r.status_code}


def _send_email(cfg: Dict[str, Any], subject: str, body: str) -> Optional[str]:
    email_cfg = _cfg_get(cfg, ["notify", "channels", "email"], {}) or {}
    if not email_cfg.get("enabled"):
        return "email disabled"
    host = email_cfg.get("smtp_host", "")
    port = int(email_cfg.get("smtp_port") or 587)
    use_tls = bool(email_cfg.get("use_tls", True))
    user = os.getenv(email_cfg.get("username_env", "") or "", "")
    pwd = os.getenv(email_cfg.get("password_env", "") or "", "")
    sender = email_cfg.get("from", "")
    to = email_cfg.get("to") or []
    if not host or not sender or not to:
        return "email misconfigured"
    try:
        msg = MIMEText(body, _subtype="plain", _charset="utf-8")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(to)
        s = smtplib.SMTP(host, port, timeout=10)
        if use_tls:
            s.starttls()
        if user:
            s.login(user, pwd)
        s.sendmail(sender, to, msg.as_string())
        s.quit()
        return None
    except Exception as e:
        return f"email error: {e}"


def _webhook_targets(cfg: Dict[str, Any]) -> List[Dict[str, str]]:
    items = _cfg_get(cfg, ["notify", "channels", "webhooks"], []) or []
    out = []
    for it in items:
        url = it.get("url")
        if not url and it.get("env"):
            url = os.getenv(it["env"], "")
        if url:
            out.append({"url": url, "kind": it.get("kind", "generic")})
    return out


def should_notify(
    cfg: Dict[str, Any],
    event: str,
    task: Optional[Dict[str, Any]] = None,
    success: Optional[bool] = None,
) -> bool:
    if not _cfg_get(cfg, ["notify", "enabled"], True):
        return False
    on_cfg = _cfg_get(cfg, ["notify", "on"], {}) or {}
    if event == "job":
        # task-level overrides?
        tset = (task or {}).get("notify") or {}
        if success is True and tset.get("on_success") is True:
            return True
        if success is False and tset.get("on_failure") is False:
            return False
        if success is True:
            return bool(on_cfg.get("job_success"))
        if success is False:
            return bool(on_cfg.get("job_failure", True))
        return False
    if event == "schedule_error":
        return bool(on_cfg.get("schedule_error", True))
    return False


async def notify_job(
    cfg: Dict[str, Any],
    result: Dict[str, Any],
    success: bool,
    task: Dict[str, Any],
    error_msg: str | None = None,
) -> None:
    if not should_notify(cfg, "job", task, success):
        return
    redact_text, _ = _redactor(cfg)
    name = result.get("name", "job")
    rc = result.get("return_code")
    dur = result.get("duration_ms")
    run_dir = result.get("run_dir_rel", "")
    stdout_rel = result.get("stdout_rel", "")
    stderr_rel = result.get("stderr_rel", "")

    # Tail stdout/stderr
    def tail(rel: str) -> str:
        try:
            p = APP_ROOT / rel
            if p.exists():
                t = p.read_text(encoding="utf-8", errors="ignore")
                return redact_text(t)
        except Exception:
            pass
        return ""

    stdout_tail = tail(stdout_rel)
    stderr_tail = tail(stderr_rel)

    subject = f"[Heimdall] Job {'OK' if success else 'FAIL'} — {name} (rc={rc}, {dur}ms)"
    text = f"""host={socket.gethostname()}
job={name}
ok={success}
rc={rc}
duration_ms={dur}
run_dir={run_dir}
stdout={stdout_rel}
stderr={stderr_rel}
error={error_msg or ''}
---
STDOUT (tail/redacted)
{stdout_tail}

---
STDERR (tail/redacted)
{stderr_tail}
"""
    payload = {"text": text}

    # webhooks
    for tgt in _webhook_targets(cfg):
        try:
            await _send_webhook(tgt["url"], tgt["kind"], payload)
        except Exception:
            pass

    # email (optional)
    _send_email(cfg, subject, text)


async def notify_schedule_error(cfg: Dict[str, Any], name: str, message: str) -> None:
    if not should_notify(cfg, "schedule_error"):
        return
    subject = f"[Heimdall] Schedule error — {name}"
    text = f"Schedule '{name}' failed to apply or run.\n\n{message}\n"
    payload = {"text": text}
    for tgt in _webhook_targets(cfg):
        try:
            await _send_webhook(tgt["url"], tgt["kind"], payload)
        except Exception:
            pass
    _send_email(cfg, subject, text)


async def notify_test(cfg: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"text": "[Heimdall] Notification test — hello!"}
    results = []
    for tgt in _webhook_targets(cfg):
        try:
            r = await _send_webhook(tgt["url"], tgt["kind"], payload)
            results.append({"target": tgt["kind"], "status": r.get("status")})
        except Exception as e:
            results.append({"target": tgt["kind"], "error": str(e)})
    err = _send_email(cfg, "[Heimdall] Notification test", "Hello from Heimdall notifier.")
    if err:
        results.append({"email": err})
    else:
        results.append({"email": "sent or disabled"})
    return {"sent": results}
