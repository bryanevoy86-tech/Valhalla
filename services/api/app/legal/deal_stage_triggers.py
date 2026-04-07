from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.legal.legal_send_service import queue_legal_document
from app.legal.recipient_registry import resolve_legal_contacts


@dataclass
class StageTriggerResult:
    triggered: bool
    stage: str
    template_key: str | None
    approval_id: str | None
    queued: bool
    reason: str | None = None
    document_path: str | None = None
    missing_fields: list[str] | None = None


STAGE_TEMPLATE_MAP: dict[str, str] = {
    "lead_qualified": "buyer_non_circumvention",
    "deal_ready_for_offer": "purchase_sale_agreement",
    "buyer_matched": "assignment_of_contract",
    "jv_mode": "jv_agreement",
    "closing_prep": "earnest_money_agreement",
}


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def build_payload_for_template(template_key: str, deal: dict[str, Any]) -> dict[str, Any]:
    today = datetime.now(timezone.utc).date().isoformat()

    common = {
        "date": deal.get("date", today),
        "seller_name": _safe_str(deal.get("seller_name")),
        "buyer_name": _safe_str(deal.get("buyer_name", deal.get("end_buyer_name"))),
        "your_company": _safe_str(deal.get("your_company", "Valhalla Legacy Inc.")),
        "property_address": _safe_str(deal.get("property_address")),
        "purchase_price": _safe_str(deal.get("purchase_price")),
        "earnest_money": _safe_str(deal.get("earnest_money")),
        "title_company": _safe_str(deal.get("title_company")),
        "inspection_days": _safe_str(deal.get("inspection_days", 10)),
        "closing_date": _safe_str(deal.get("closing_date")),
        "additional_terms": _safe_str(
            deal.get("additional_terms", "Subject to lawyer review before final execution.")
        ),
        "contract_date": _safe_str(deal.get("contract_date", today)),
        "assignment_fee": _safe_str(deal.get("assignment_fee")),
        "agreement_term": _safe_str(deal.get("agreement_term", "12 months")),
        "partner_name": _safe_str(deal.get("partner_name")),
        "your_split": _safe_str(deal.get("your_split")),
        "partner_split": _safe_str(deal.get("partner_split")),
        "roles": _safe_str(deal.get("roles")),
    }

    template_specific: dict[str, Any] = {}

    if template_key == "purchase_sale_agreement":
        template_specific = {
            "buyer_name": common["your_company"] if not common["buyer_name"] else common["buyer_name"],
        }

    elif template_key == "assignment_of_contract":
        template_specific = {
            "buyer_name": _safe_str(deal.get("end_buyer_name", deal.get("buyer_name"))),
        }

    elif template_key == "buyer_non_circumvention":
        template_specific = {
            "buyer_name": _safe_str(deal.get("end_buyer_name", deal.get("buyer_name"))),
        }

    elif template_key == "jv_agreement":
        template_specific = {
            "partner_name": _safe_str(deal.get("partner_name")),
            "your_split": _safe_str(deal.get("your_split", 50)),
            "partner_split": _safe_str(deal.get("partner_split", 50)),
            "roles": _safe_str(deal.get("roles", "To be finalized in lawyer review.")),
        }

    elif template_key == "earnest_money_agreement":
        template_specific = {
            "buyer_name": _safe_str(deal.get("end_buyer_name", deal.get("buyer_name", deal.get("your_company")))),
        }

    payload = {**common, **template_specific}
    return payload


def default_recipients_for_stage(stage: str, deal: dict[str, Any]) -> tuple[list[str], list[str], dict[str, Any]]:
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

    # Explicit payload values override registry if present
    if deal.get("lawyer_email") and deal["lawyer_email"] not in recipients:
        recipients.insert(0, deal["lawyer_email"])

    if deal.get("title_company_email") and deal["title_company_email"] not in recipients:
        recipients.append(deal["title_company_email"])

    if deal.get("accountant_email") and deal["accountant_email"] not in cc:
        cc.append(deal["accountant_email"])

    # Fill title company name from registry if not passed
    if not deal.get("title_company") and resolved.get("title_company"):
        deal["title_company"] = resolved["title_company"]

    return recipients, cc, resolved


def queue_legal_for_stage(stage: str, deal: dict[str, Any]) -> StageTriggerResult:
    template_key = STAGE_TEMPLATE_MAP.get(stage)
    if not template_key:
        return StageTriggerResult(
            triggered=False,
            stage=stage,
            template_key=None,
            approval_id=None,
            queued=False,
            reason=f"No template mapped for stage: {stage}",
        )

    approval_id = f"{deal.get('deal_id', 'unknown')}__{stage}__{template_key}"

    recipients, cc, resolved = default_recipients_for_stage(stage, deal)

    if not deal.get("title_company") and resolved.get("title_company"):
        deal["title_company"] = resolved["title_company"]

    payload = build_payload_for_template(template_key, deal)

    if not recipients:
        return StageTriggerResult(
            triggered=False,
            stage=stage,
            template_key=template_key,
            approval_id=approval_id,
            queued=False,
            reason="No legal recipients configured",
        )

    result = queue_legal_document(
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

    return StageTriggerResult(
        triggered=True,
        stage=stage,
        template_key=template_key,
        approval_id=approval_id,
        queued=result.get("queued", False),
        document_path=result.get("document_path"),
        missing_fields=result.get("missing_fields", []),
        reason=None,
    )


def get_stage_template_map() -> dict[str, str]:
    return STAGE_TEMPLATE_MAP.copy()
