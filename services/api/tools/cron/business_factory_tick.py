"""Optional no-AI Business Factory cron tick.

Designed for the existing daily-email Render cron container. The tick is
DISABLED unless both factory URL and owner key have been explicitly configured.
It can only call the known Valhalla API host/path over HTTPS and never follows
redirects with the secret header.
"""
from __future__ import annotations

import json
import os
import re
from urllib.parse import urlparse
import urllib.error
import urllib.request

EXPECTED_PATH = "/api/business-factory/actions/run-once"
DEFAULT_ALLOWED_HOST = "valhalla-api-ha6a.onrender.com"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def run_factory_tick() -> dict:
    url = os.getenv("BUSINESS_FACTORY_RUN_URL", "").strip()
    key = os.getenv("VALHALLA_FACTORY_KEY", "").strip()

    if not url and not key:
        return {"status": "skipped", "reason": "not_configured", "verified": False}

    if not url or not key:
        raise RuntimeError("Business Factory cron configuration incomplete")

    parts = urlparse(url)
    allowed_host = os.getenv("BUSINESS_FACTORY_ALLOWED_HOST", DEFAULT_ALLOWED_HOST)
    if (
        parts.scheme != "https"
        or parts.hostname != allowed_host
        or parts.port is not None
        or parts.username is not None
        or parts.password is not None
        or parts.path != EXPECTED_PATH
        or parts.query
        or parts.fragment
    ):
        raise RuntimeError("Business Factory run URL did not pass strict allowlist")

    opener = urllib.request.build_opener(_NoRedirect)
    request = urllib.request.Request(
        url=url,
        method="POST",
        data=b"",
        headers={
            "X-Business-Factory-Key": key,
            "Content-Type": "application/json",
        },
    )
    try:
        with opener.open(request, timeout=30) as response:
            if response.status != 200:
                raise RuntimeError(f"Business Factory unexpected status {response.status}")
            data = json.loads(response.read(20_000).decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Never print the private factory key, request headers, or response body.
        raise RuntimeError(f"Business Factory HTTP status {exc.code}") from None
    except (ValueError, OSError) as exc:
        raise RuntimeError(f"Business Factory request or response failure: {type(exc).__name__}") from None

    if not isinstance(data, dict):
        raise RuntimeError("Business Factory worker did not confirm a valid internal result")
    status = data.get("status")
    if status == "idle" and data.get("verified") is False:
        return {"status": "idle", "verified": False}
    if status == "blocked" and data.get("verified") is False:
        return {"status": "blocked", "verified": False,
                "emergency_stop": data.get("reason") == "EMERGENCY_STOP_ACTIVE"}
    if status == "completed" and data.get("verified") is True:
        receipt = data.get("receipt")
        if (
            isinstance(receipt, dict)
            and receipt.get("verification_scope") == "database_artifact_only"
            and receipt.get("artifact_type") == "product_listing_draft"
            and type(receipt.get("external_effects")) is int
            and receipt["external_effects"] == 0
            and receipt.get("sales_verified") is False
            and type(receipt.get("media_content_id")) is int
            and receipt["media_content_id"] > 0
            and isinstance(receipt.get("action_id"), str)
            and re.fullmatch(r"bfd_[0-9a-f]{32}", receipt["action_id"])
            and isinstance(receipt.get("sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", receipt["sha256"])
        ):
            return {
                "status": "internal_artifact_verified",
                "verified": True,
                "action_id": receipt.get("action_id"),
            }
    raise RuntimeError("Business Factory worker did not confirm a valid internal result")
