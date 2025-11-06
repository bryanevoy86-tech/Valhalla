import os
from typing import Any, Dict
from app.providers.base import ProviderAdapter


class DocusignAdapter(ProviderAdapter):
    name = "docusign"

    def health(self) -> Dict[str, Any]:
        return {
            "ok": all(
                [
                    os.getenv("DOCUSIGN_INTEGRATOR_KEY"),
                    os.getenv("DOCUSIGN_USER_ID"),
                    os.getenv("DOCUSIGN_ACCOUNT_ID"),
                    os.getenv("DOCUSIGN_BASE_URI"),
                ]
            )
        }

    def validate_signature(self, body: bytes, signature: str | None) -> bool:
        # Replace with DocuSign Connect HMAC validation when turning on prod
        expected = os.getenv("DOCUSIGN_WEBHOOK_SECRET")
        return bool(expected) and signature == expected
