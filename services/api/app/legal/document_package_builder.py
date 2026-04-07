from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.legal.legal_send_service import queue_legal_document
from app.legal.recipient_registry import resolve_legal_contacts
from app.legal.deal_stage_triggers import build_payload_for_template


@dataclass
class PackageBuildResult:
    package_id: str
    stage: str
    triggered: bool
    queued_count: int
    documents: list[dict[str, Any]]
    reason: str | None = None


STAGE_PACKAGE_MAP: dict[str, list[str]] = {
    "lead_qualified": [
        "buyer_non_circumvention"
    ],
    "deal_ready_for_offer": [
        "purchase_sale_agreement",
        "property_disclosure_acknowledgment",
        "earnest_money_agreement"
    ],
    "buyer_matched": [
        "assignment_of_contract",
        "property_disclosure_acknowledgment"
    ],
    "jv_mode": [
        "jv_agreement"
    ],
    "closing_prep": [
        "earnest_money_agreement",
        "property_disclosure_acknowledgment"
    ]
}


def get_stage_package_map() -> dict[str, list[str]]:
    return STAGE_PACKAGE_MAP.copy()


def _resolve_package_contacts(deal: dict[str, Any]) -> tuple[list[str], list[str], dict[str, Any]]:
    company_name = deal.get("your_company", "Valhalla Legacy Inc.")
    region_code = deal.get("region_code", "")
    deal_type = deal.get("deal_type", "wholesale")

    resolved = resolve_legal_contacts(
        company_name=company_name,
        region_code=region_code,
        deal_type=deal_type,
    )

    recipients = list(resolved.get("recipients", []))
    cc = list(resolved.get("cc", []))

    if deal.get("lawyer_email") and deal["lawyer_email"] not in recipients:
        recipients.insert(0, deal["lawyer_email"])

    if deal.get("title_company_email") and deal["title_company_email"] not in recipients:
        recipients.append(deal["title_company_email"])

    if deal.get("accountant_email") and deal["accountant_email"] not in cc:
        cc.append(deal["accountant_email"])

    if not deal.get("title_company") and resolved.get("title_company"):
        deal["title_company"] = resolved["title_company"]

    return recipients, cc, resolved


def queue_legal_package_for_stage(stage: str, deal: dict[str, Any]) -> PackageBuildResult:
    templates = STAGE_PACKAGE_MAP.get(stage)
    if not templates:
        return PackageBuildResult(
            package_id=f"{deal.get('deal_id', 'unknown')}__{stage}",
            stage=stage,
            triggered=False,
            queued_count=0,
            documents=[],
            reason=f"No package mapped for stage: {stage}",
        )

    recipients, cc, resolved = _resolve_package_contacts(deal)

    if not recipients:
        return PackageBuildResult(
            package_id=f"{deal.get('deal_id', 'unknown')}__{stage}",
            stage=stage,
            triggered=False,
            queued_count=0,
            documents=[],
            reason="No legal recipients configured",
        )

    if not deal.get("title_company") and resolved.get("title_company"):
        deal["title_company"] = resolved["title_company"]

    package_id = f"{deal.get('deal_id', 'unknown')}__{stage}__package"
    results: list[dict[str, Any]] = []

    for template_key in templates:
        payload = build_payload_for_template(template_key, deal)
        approval_id = f"{deal.get('deal_id', 'unknown')}__{stage}__{template_key}"

        queued = queue_legal_document(
            approval_id=approval_id,
            template_key=template_key,
            payload=payload,
            recipients=recipients,
            cc=cc,
            body_intro=deal.get(
                "legal_body_intro",
                f"Please review and finalize this {template_key} draft for {deal.get('property_address', 'the deal')}.",
            ),
        )

        results.append(
            {
                "approval_id": approval_id,
                "template_key": template_key,
                "queued": queued.get("queued", False),
                "document_path": queued.get("document_path"),
                "missing_fields": queued.get("missing_fields", []),
                "subject": queued.get("subject"),
            }
        )

    queued_count = sum(1 for item in results if item.get("queued") is True)

    return PackageBuildResult(
        package_id=package_id,
        stage=stage,
        triggered=True,
        queued_count=queued_count,
        documents=results,
        reason=None,
    )
