from __future__ import annotations

import re
from typing import Any, Dict


EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
# Phone: requires at least one hyphen/space/paren separator to avoid false positives with long digit strings
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]+[2-9]\d{2}[-.\s]+\d{4}")
LONG_DIGITS_RE = re.compile(r"\b\d{13,}\b")  # Account-like, 13+ digits


def redact_text(text: str, level: str = "shareable") -> Dict[str, Any]:
    s = text or ""

    # shareable: mask common PII - order matters!
    s2 = EMAIL_RE.sub("[REDACTED_EMAIL]", s)
    s2 = LONG_DIGITS_RE.sub("[REDACTED_NUMBER]", s2)  # Long digits first
    s2 = PHONE_RE.sub("[REDACTED_PHONE]", s2)  # Then phone

    if level == "strict":
        # also mask street-ish patterns lightly
        s2 = re.sub(r"\b(\d{1,5}\s+\w+(\s+\w+){0,4}\s+(st|street|ave|avenue|rd|road|blvd|boulevard|dr|drive|ln|lane))\b",
                    "[REDACTED_ADDRESS]", s2, flags=re.I)

    return {"redacted": s2, "meta": {"level": level}}


def sanitize_manifest(manifest: Dict[str, Any], level: str = "shareable") -> Dict[str, Any]:
    """
    Removes sensitive transport refs for shareable exports.
    """
    out = dict(manifest or {})
    docs = []
    for d in (out.get("docs") or []):
        d2 = dict(d)
        # always remove machine refs
        d2.pop("file_path", None)
        d2.pop("blob_ref", None)
        d2.pop("sha256", None)

        # redact notes if strict/shareable
        if level in ("shareable", "strict") and "notes" in d2 and isinstance(d2["notes"], str):
            d2["notes"] = redact_text(d2["notes"], level=level)["redacted"]

        docs.append(d2)

    out["docs"] = docs
    out["sanitized"] = True
    out["sanitized_level"] = level
    return out
