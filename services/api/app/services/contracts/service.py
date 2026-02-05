from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.contracts import (
    Contract,
    ContractTemplate,
    ContractParty,
    ContractPartyRole,
    ContractDocument,
    ContractDocKind,
    ContractEnvelope,
    ContractEvent,
    ContractState,
    SignProvider,
)
from app.schemas.contracts import PartyIn
from app.services.contracts.provider_base import ProviderRecipient, SignatureProvider
from app.services.contracts.provider_sandbox import SandboxSignatureProvider


def _id() -> str:
    return uuid.uuid4().hex


ALLOWED_TRANSITIONS = {
    ContractState.DRAFT: {ContractState.READY_FOR_REVIEW, ContractState.VOIDED},
    ContractState.READY_FOR_REVIEW: {ContractState.IN_REVIEW, ContractState.DRAFT, ContractState.VOIDED},
    ContractState.IN_REVIEW: {
        ContractState.APPROVED_FOR_SIGNATURE,
        ContractState.DRAFT,
        ContractState.VOIDED,
    },
    ContractState.APPROVED_FOR_SIGNATURE: {ContractState.SENT_FOR_SIGNATURE, ContractState.VOIDED},
    ContractState.SENT_FOR_SIGNATURE: {
        ContractState.PARTIALLY_SIGNED,
        ContractState.FULLY_EXECUTED,
        ContractState.DECLINED,
        ContractState.VOIDED,
    },
    ContractState.PARTIALLY_SIGNED: {ContractState.FULLY_EXECUTED, ContractState.DECLINED, ContractState.VOIDED},
    ContractState.FULLY_EXECUTED: {ContractState.ARCHIVED},
    ContractState.DECLINED: {ContractState.ARCHIVED},
    ContractState.VOIDED: {ContractState.ARCHIVED},
    ContractState.ARCHIVED: set(),
}


class ContractPipeline:
    def __init__(self, db: Session):
        self.db = db
        self.storage = self._resolve_storage()
        self.provider = self._resolve_provider()

    def _resolve_storage(self):
        """Resolve storage backend: S3 (default) or local."""
        backend = os.getenv("CONTRACT_STORAGE_BACKEND", "s3").lower().strip()
        if backend == "s3":
            from app.services.contracts.storage_s3 import S3ContractStorage
            return S3ContractStorage()
        else:
            from app.services.contracts.storage import LocalContractStorage
            return LocalContractStorage(os.getenv("CONTRACT_STORAGE_LOCAL_DIR", "./.contract_store"))

    def _resolve_provider(self) -> SignatureProvider:
        p = os.getenv("SIGN_PROVIDER", "sandbox").lower().strip()
        return SandboxSignatureProvider()

    def _event(self, contract_id: str, event_type: str, actor: Optional[str], meta: Dict[str, Any]) -> None:
        self.db.add(
            ContractEvent(
                id=_id(),
                contract_id=contract_id,
                event_type=event_type,
                actor=actor,
                meta=meta,
            )
        )
        self.db.flush()

    def create_contract(
        self,
        template_code: str,
        title: str,
        deal_id: Optional[str],
        zone_id: Optional[str],
        merge_data: Dict[str, Any],
        parties: List[PartyIn],
        sign_provider: SignProvider,
        actor: Optional[str],
    ) -> Contract:
        tpl = self.db.query(ContractTemplate).filter(ContractTemplate.code == template_code).one_or_none()
        if not tpl:
            raise ValueError(f"Unknown template_code: {template_code}")

        c = Contract(
            id=_id(),
            template_id=tpl.id,
            title=title,
            state=ContractState.DRAFT,
            deal_id=deal_id,
            zone_id=zone_id,
            merge_data=merge_data,
            sign_provider=sign_provider,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(c)
        self.db.flush()

        for p in parties:
            self.db.add(
                ContractParty(
                    id=_id(),
                    contract_id=c.id,
                    role=p.role,
                    name=p.name,
                    email=str(p.email) if p.email else None,
                    phone=p.phone,
                    must_sign=p.must_sign,
                    created_at=datetime.utcnow(),
                )
            )
        self._event(c.id, "CONTRACT_CREATED", actor, {"template_code": template_code})
        self.db.commit()
        return c

    def change_state(
        self,
        contract_id: str,
        target: ContractState,
        actor: Optional[str],
        note: Optional[str],
    ) -> Contract:
        c = self.db.query(Contract).filter(Contract.id == contract_id).one()
        allowed = ALLOWED_TRANSITIONS.get(c.state, set())
        if target not in allowed:
            raise ValueError(f"Invalid transition {c.state} -> {target}")
        prev = c.state
        c.state = target
        c.updated_at = datetime.utcnow()
        self._event(c.id, "STATE_CHANGED", actor, {"from": prev, "to": target, "note": note})
        self.db.commit()
        return c

    def upload_document(
        self,
        contract_id: str,
        filename: str,
        content_type: str,
        kind: ContractDocKind,
        data: bytes,
        actor: Optional[str],
    ) -> ContractDocument:
        c = self.db.query(Contract).filter(Contract.id == contract_id).one()
        stored = self.storage.put_bytes(contract_id=c.id, filename=filename, data=data)

        doc = ContractDocument(
            id=_id(),
            contract_id=c.id,
            kind=kind,
            filename=filename,
            content_type=content_type,
            storage_key=stored.storage_key,
            sha256=stored.sha256,
            bytes=stored.size_bytes,
            created_at=datetime.utcnow(),
        )
        self.db.add(doc)
        self._event(c.id, "DOC_UPLOADED", actor, {"doc_id": doc.id, "kind": kind, "filename": filename})
        self.db.commit()
        return doc

    def _latest_draft_pdf(self, contract_id: str) -> bytes:
        doc = (
            self.db.query(ContractDocument)
            .filter(
                ContractDocument.contract_id == contract_id,
                ContractDocument.kind == ContractDocKind.DRAFT,
            )
            .order_by(ContractDocument.created_at.desc())
            .first()
        )
        if not doc:
            raise ValueError("No DRAFT document uploaded/generated yet.")
        return self.storage.get_bytes(doc.storage_key)

    def send_for_signature(
        self,
        contract_id: str,
        subject: str,
        message: str,
        actor: Optional[str],
    ) -> ContractEnvelope:
        c = self.db.query(Contract).filter(Contract.id == contract_id).one()
        if c.state != ContractState.APPROVED_FOR_SIGNATURE:
            raise ValueError(f"Contract must be APPROVED_FOR_SIGNATURE to send. Current={c.state}")

        pdf = self._latest_draft_pdf(contract_id)
        parties = (
            self.db.query(ContractParty)
            .filter(ContractParty.contract_id == contract_id, ContractParty.must_sign == True)
            .all()
        )
        recipients = []
        for p in parties:
            if not p.email:
                raise ValueError(f"Missing email for signer: {p.name} ({p.role})")
            recipients.append(ProviderRecipient(name=p.name, email=p.email, role=str(p.role.value)))

        sandbox_mode = os.getenv("SANDBOX", "1").lower() in {"1", "true", "yes", "on"}

        result = self.provider.create_and_send_envelope(
            contract_id=contract_id,
            subject=subject,
            message=message,
            pdf_bytes=pdf,
            recipients=recipients,
            sandbox=sandbox_mode,
        )

        env = ContractEnvelope(
            id=_id(),
            contract_id=contract_id,
            provider=SignProvider.SANDBOX if result.provider == "sandbox" else SignProvider.DOCUSIGN,
            provider_envelope_id=result.provider_envelope_id,
            status=result.status,
            raw=result.raw,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(env)

        c.active_envelope_id = env.id
        c.state = ContractState.SENT_FOR_SIGNATURE
        c.updated_at = datetime.utcnow()

        self._event(
            c.id,
            "ENVELOPE_SENT",
            actor,
            {
                "envelope_id": env.id,
                "provider_envelope_id": env.provider_envelope_id,
                "status": env.status,
            },
        )
        self.db.commit()
        return env
