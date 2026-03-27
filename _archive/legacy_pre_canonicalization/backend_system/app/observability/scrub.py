import json
import os
import re
from typing import Any, Dict

ENABLED = os.getenv("SCRUB_ENABLED", "false").lower() in ("1", "true", "yes")
REPL = os.getenv("SCRUB_REPLACEMENT", "***REDACTED***")
MAX_PREVIEW = int(os.getenv("SCRUB_BODY_MAX_PREVIEW", "8192"))


def _split_env(name: str) -> list[str]:
    v = os.getenv(name, "").strip()
    if not v:
        return []
    return [x.strip() for x in v.split(",") if x.strip()]


ALLOW_KEYS = set(k.lower() for k in _split_env("SCRUB_ALLOW_KEYS"))
_DENY_RAW = _split_env("SCRUB_DENY_KEYS")
_DENY_EXACT = set()
_DENY_REGEX: list[re.Pattern] = []
for k in _DENY_RAW:
    if len(k) >= 2 and k[0] == "/" and k[-1] == "/":
        try:
            _DENY_REGEX.append(re.compile(k[1:-1], re.IGNORECASE))
        except Exception:
            pass
    else:
        _DENY_EXACT.add(k.lower())

PATTERNS_ENABLED = os.getenv("SCRUB_PATTERNS", "true").lower() in ("1", "true", "yes")
_PATTERNS: list[re.Pattern] = []
if PATTERNS_ENABLED:
    _PATTERNS = [
        re.compile(r"(?i)\b(bearer\s+|token[:=]\s*)([A-Za-z0-9\-_\.]{10,})"),
        re.compile(r"(?i)\b(AKIA|ASIA)[A-Z0-9]{16}\b"),
        re.compile(r"(?i)\baws_secret_access_key\b\s*[:=]\s*[A-Za-z0-9/+=]{35,45}"),
        re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
        re.compile(r"(?<!\d)(\+?\d[\d\-\s\(\)]{8,}\d)"),
        re.compile(r"(?<!\d)(\d[ -]?){13,19}(?!\d)"),
        re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)"),
        re.compile(
            r"(?i)\b(client_secret|refresh_token|access_token)\b\s*[:=]\s*[A-Za-z0-9\-_\.~]{16,}"
        ),
    ]


def _scrub_text(s: str) -> str:
    if not PATTERNS_ENABLED or not s:
        return s
    t = s
    for rx in _PATTERNS:
        t = rx.sub(lambda m: (m.group(1) if m.lastindex == 2 else "") + REPL, t)
    return t


def _should_scrub_key(key: str) -> bool:
    kl = (key or "").lower()
    if kl in ALLOW_KEYS:
        return False
    if kl in _DENY_EXACT:
        return True
    for rx in _DENY_REGEX:
        if rx.search(kl):
            return True
    return False


def scrub_mapping(obj: Dict[str, Any]) -> Dict[str, Any]:
    if not ENABLED or not isinstance(obj, dict):
        return obj
    out: Dict[str, Any] = {}
    for k, v in obj.items():
        if _should_scrub_key(k):
            out[k] = REPL
            continue
        out[k] = scrub_any(v)
    return out


def scrub_any(v: Any) -> Any:
    if not ENABLED:
        return v
    if isinstance(v, dict):
        return scrub_mapping(v)
    if isinstance(v, list):
        return [scrub_any(x) for x in v]
    if isinstance(v, str):
        if len(v) > MAX_PREVIEW:
            return _scrub_text(v[:MAX_PREVIEW]) + f"…(truncated {len(v)-MAX_PREVIEW} bytes)"
        return _scrub_text(v)
    try:
        js = json.dumps(v)
        return json.loads(_scrub_text(js))
    except Exception:
        return v


def scrub_headers(h: Dict[str, str]) -> Dict[str, str]:
    if not ENABLED or not isinstance(h, dict):
        return h
    out = {}
    for k, v in h.items():
        out[k] = REPL if _should_scrub_key(k) else (_scrub_text(v) if isinstance(v, str) else v)
    return out


def scrub_json_text_maybe(s: str) -> str:
    if not ENABLED or not s:
        return s
    try:
        val = json.loads(s)
        scrubbed = scrub_any(val)
        return json.dumps(scrubbed, ensure_ascii=False)
    except Exception:
        return _scrub_text(s)
