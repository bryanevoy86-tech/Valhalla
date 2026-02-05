from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Any, List
from .provider_base import SignatureProvider, ProviderRecipient, ProviderCreateEnvelopeResult


class SandboxSignatureProvider(SignatureProvider):
    def create_and_send_envelope(
        self,
        contract_id: str,
        subject: str,
        message: str,
        pdf_bytes: bytes,
        recipients: List[ProviderRecipient],
        sandbox: bool,
    ) -> ProviderCreateEnvelopeResult:
        env_id = f"sandbox_{uuid.uuid4().hex}"
        return ProviderCreateEnvelopeResult(
            provider="sandbox",
            provider_envelope_id=env_id,
            status="sent" if not sandbox else "queued_sandbox",
            raw={
                "contract_id": contract_id,
                "subject": subject,
                "message": message,
                "recipient_count": len(recipients),
                "bytes": len(pdf_bytes),
                "created_at": datetime.utcnow().isoformat(),
            },
        )

    def parse_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        return {
            "provider_envelope_id": payload.get("provider_envelope_id"),
            "status": payload.get("status", "unknown"),
            "recipients": payload.get("recipients", []),
            "raw": payload,
        }
