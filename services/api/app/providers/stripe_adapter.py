"""Stripe provider: verify authentic signed webhook payloads.

Stripe signing protocol uses Stripe-Signature: t=UNIX_TIME,v1=HEX_HMAC_SHA256.
Hash input is the exact byte sequence "timestamp.rawBody"; no reconstructed JSON.
This adapter verifies authenticity only; payment settlement requires a
separate idempotent and reconciled financial handler.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Any, Dict

from app.providers.base import ProviderAdapter


def verify_stripe_signature(
    body: bytes,
    signature: str | None,
    secret: str | None,
    *,
    now: int | None = None,
    tolerance_seconds: int = 300,
) -> bool:
    if not isinstance(body, bytes) or not signature or not secret:
        return False
    if tolerance_seconds <= 0:
        return False
    entries: dict[str, list[str]] = {}
    for fragment in signature.split(","):
        key, sep, value = fragment.strip().partition("=")
        if sep:
            entries.setdefault(key, []).append(value)
    times = entries.get("t", [])
    signatures = entries.get("v1", [])
    if len(times) != 1 or not signatures or not times[0].isdigit():
        return False
    timestamp = int(times[0])
    current = int(time.time()) if now is None else now
    if abs(current - timestamp) > tolerance_seconds:
        return False
    signed = times[0].encode("ascii") + b"." + body
    digest = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return any(
        len(candidate) == len(digest) and hmac.compare_digest(digest, candidate)
        for candidate in signatures
    )


class StripeAdapter(ProviderAdapter):
    name = "stripe"

    def health(self) -> Dict[str, Any]:
        return {
            "ok": bool(os.getenv("STRIPE_SECRET_KEY")),
            "webhook": bool(os.getenv("STRIPE_WEBHOOK_SECRET")),
        }

    def validate_signature(self, body: bytes, signature: str | None) -> bool:
        return verify_stripe_signature(body, signature, os.getenv("STRIPE_WEBHOOK_SECRET"))
