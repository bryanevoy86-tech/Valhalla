from __future__ import annotations

from typing import Any

from app.legal.approval_send_orchestrator import approve_and_send_legal_document
from app.legal.document_package_builder import STAGE_PACKAGE_MAP


def approve_and_send_package(stage: str, deal_id: str) -> dict[str, Any]:
    templates = STAGE_PACKAGE_MAP.get(stage, [])
    if not templates:
        return {
            "package_sent": False,
            "stage": stage,
            "deal_id": deal_id,
            "reason": f"No package mapped for stage: {stage}",
            "results": []
        }

    results = []
    sent_count = 0

    for template_key in templates:
        approval_id = f"{deal_id}__{stage}__{template_key}"
        result = approve_and_send_legal_document(approval_id)
        results.append({
            "approval_id": approval_id,
            **result
        })
        if result.get("sent") is True:
            sent_count += 1

    return {
        "package_sent": sent_count == len(templates),
        "stage": stage,
        "deal_id": deal_id,
        "sent_count": sent_count,
        "total_count": len(templates),
        "results": results,
    }
