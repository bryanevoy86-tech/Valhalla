from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class ProviderRecipient:
    name: str
    email: str
    role: str
    recipient_id: Optional[str] = None


@dataclass
class ProviderCreateEnvelopeResult:
    provider: str
    provider_envelope_id: str
    status: str
    raw: Dict[str, Any]


class SignatureProvider(ABC):
    @abstractmethod
    def create_and_send_envelope(
        self,
        contract_id: str,
        subject: str,
        message: str,
        pdf_bytes: bytes,
        recipients: List[ProviderRecipient],
        sandbox: bool,
    ) -> ProviderCreateEnvelopeResult:
        raise NotImplementedError

    @abstractmethod
    def parse_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Return normalized event: {provider_envelope_id, status, recipients:[{email,signed_at?}], raw}"""
        raise NotImplementedError
