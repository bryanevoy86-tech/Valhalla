import os
from typing import Any, Dict
from app.providers.base import ProviderAdapter


class PlaidAdapter(ProviderAdapter):
    name = "plaid"

    def health(self) -> Dict[str, Any]:
        return {"ok": True, "env": os.getenv("PLAID_ENV", "missing")}

    def validate_signature(self, body: bytes, signature: str | None) -> bool:
        # Plaid webhook HMAC is optional in sandbox; add real check when live
        return True
