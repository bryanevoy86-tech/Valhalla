from __future__ import annotations

from app.finance.finance_control_service import (
    queue_financial_intent_for_approval,
    approve_financial_intent,
    set_finance_freeze,
)


def test_queue_financial_intent():
    result = queue_financial_intent_for_approval(
        deal_id="DEAL-100",
        intent_id="INTENT-100",
        amount=5000,
        purpose="earnest_money",
        payee="title_company",
        requested_by="heimdall",
    )
    assert result["queued"] is True
    assert result["blocked"] is False


def test_approve_financial_intent():
    queue_financial_intent_for_approval(
        deal_id="DEAL-101",
        intent_id="INTENT-101",
        amount=2500,
        purpose="assignment_fee_partial",
        payee="Valhalla Legacy Inc.",
        requested_by="heimdall",
    )
    result = approve_financial_intent("INTENT-101", "bryan")
    assert result["approved"] is True


def test_freeze_blocks_new_intent():
    set_finance_freeze(True, "manual hold")
    result = queue_financial_intent_for_approval(
        deal_id="DEAL-102",
        intent_id="INTENT-102",
        amount=1000,
        purpose="test_hold",
        payee="seller",
        requested_by="heimdall",
    )
    assert result["blocked"] is True
    set_finance_freeze(False, None)
