import os
import hmac
import hashlib
from typing import Any, Dict
from app.providers.base import ProviderAdapter


class StripeAdapter(ProviderAdapter):
    name = "stripe"

    def health(self) -> Dict[str, Any]:
        return {
            "ok": bool(os.getenv("STRIPE_SECRET_KEY")),
            "webhook": bool(os.getenv("STRIPE_WEBHOOK_SECRET")),
        }

    def validate_signature(self, body: bytes, signature: str | None) -> bool:
        secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not secret or not signature:
            return False
        # simple HMAC check (illustrative; Stripe uses signed headers w/ timestamp)
        digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return digest == signature
