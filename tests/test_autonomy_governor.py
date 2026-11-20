"""Heimdall risk governor: deterministic, no AI tokens, no external effects."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))
from app.core.autonomy_governor import ActionIntent, decide  # noqa: E402


def context(action="INTERNAL_DRAFT", **overrides):
    data = {
        "action": action,
        "mode": "SHADOW",
        "action_id": "test-act",
        "business_id": "test-business",
        "legacy_id": "test-legacy",
        "business_scope_verified": True,
        "tenant_scope_verified": True,
        "owner_approval_verified": True,
        "source_rights_verified": True,
        "independent_sources": 2,
        "confidence": .92,
        "planned_cost_cents": 0,
        "remaining_budget_cents": 0,
        "consent_verified": True,
    }
    data.update(overrides)
    return ActionIntent(**data)


class AutonomyGovernorTests(unittest.TestCase):
    def test_approved_internal_draft_allowed_in_shadow(self):
        d = decide(context())
        self.assertEqual(d.verdict, "ALLOW")
        self.assertFalse(d.external_effects_authorized)

    def test_missing_owner_approval_requires_review(self):
        self.assertEqual(
            decide(context(owner_approval_verified=False)).verdict,
            "REVIEW_REQUIRED",
        )

    def test_kill_switch_blocks_even_internal_approved_work(self):
        for changed in ({"mode": "HALTED"}, {"emergency_stop": True}):
            with self.subTest(changed=changed):
                d = decide(context(**changed))
                self.assertEqual(d.verdict, "BLOCK")
                self.assertEqual(d.reason, "EMERGENCY_STOP_ACTIVE")

    def test_spend_must_be_within_budget_even_for_internal_work(self):
        d = decide(context(planned_cost_cents=10, remaining_budget_cents=9))
        self.assertEqual(d.verdict, "BLOCK")
        self.assertEqual(d.reason, "BUDGET_EXCEEDED")

    def test_circuit_breaker_and_uncertain_outcome_prevent_retries(self):
        self.assertEqual(
            decide(context(circuit_breaker_open=True)).reason,
            "CIRCUIT_BREAKER_OPEN",
        )
        self.assertEqual(
            decide(context(outcome_uncertain=True)).reason,
            "PRIOR_OUTCOME_UNKNOWN_RECONCILE_FIRST",
        )

    def test_untrusted_web_text_cannot_issue_tool_commands(self):
        d = decide(context(untrusted_source_requests_tool_action=True))
        self.assertEqual(d.verdict, "BLOCK")
        self.assertEqual(d.reason, "UNTRUSTED_SOURCE_INSTRUCTION")

    def test_cross_business_and_tenant_scope_missing_blocks(self):
        for changed in ({"business_scope_verified": False}, {"tenant_scope_verified": False}):
            with self.subTest(changed=changed):
                self.assertEqual(decide(context(**changed)).verdict, "BLOCK")

    def test_shadow_external_operations_cannot_run(self):
        for action in (
            "EXTERNAL_POST", "CUSTOMER_OUTREACH", "CUSTOMER_SUPPORT",
            "PAYMENT_CAPTURE", "PAYOUT", "CONTRACT_SIGN",
            "CODE_DEPLOY", "DELETE_CUSTOMER_DATA",
        ):
            with self.subTest(action=action):
                d = decide(context(action))
                self.assertEqual(d.verdict, "BLOCK")
                self.assertEqual(d.reason, "SHADOW_MODE_NO_EXTERNAL_EFFECTS")

    def test_bounded_high_impact_still_requires_owner_review(self):
        for action in ("PAYMENT_CAPTURE", "PAYOUT", "CONTRACT_SIGN", "CODE_DEPLOY"):
            with self.subTest(action=action):
                d = decide(context(action, mode="BOUNDED"))
                self.assertEqual(d.verdict, "REVIEW_REQUIRED")
                self.assertFalse(d.external_effects_authorized)

    def test_outreach_requires_real_consent_evidence(self):
        d = decide(context("CUSTOMER_OUTREACH", mode="BOUNDED", consent_verified=False))
        self.assertEqual(d.verdict, "BLOCK")
        self.assertEqual(d.reason, "OUTREACH_CONSENT_NOT_VERIFIED")

    def test_external_publication_remains_review_only_even_with_evidence(self):
        d = decide(context("EXTERNAL_POST", mode="BOUNDED"))
        self.assertEqual(d.verdict, "REVIEW_REQUIRED")
        self.assertEqual(d.reason, "EXTERNAL_PROVIDER_GATE_NOT_CONNECTED")

    def test_low_evidence_causes_abstention_not_confident_decision(self):
        d = decide(context("EVALUATE", independent_sources=1))
        self.assertEqual(d.verdict, "ABSTAIN")
        self.assertEqual(d.reason, "INDEPENDENT_EVIDENCE_OR_CONFIDENCE_INSUFFICIENT")
        d = decide(context("EVALUATE", confidence=.74))
        self.assertEqual(d.verdict, "ABSTAIN")
        self.assertEqual(decide(context("EVALUATE", confidence=.93)).verdict, "ALLOW")

    def test_unlicensed_source_causes_abstention(self):
        d = decide(context("RESEARCH_READ", source_rights_verified=False))
        self.assertEqual(d.verdict, "ABSTAIN")
        self.assertEqual(decide(context("RESEARCH_READ")).verdict, "ALLOW")

    def test_unknown_action_or_invalid_numeric_inputs_block(self):
        self.assertEqual(decide(context("UNKNOWN_ACTION")).verdict, "BLOCK")
        for bad in (
            {"confidence": 2.0}, {"confidence": True},
            {"planned_cost_cents": -1}, {"remaining_budget_cents": False},
            {"independent_sources": -1},
        ):
            with self.subTest(bad=bad):
                self.assertEqual(decide(context(**bad)).verdict, "BLOCK")

    def test_policy_decision_never_claims_external_authorization(self):
        for action in ("INTERNAL_DRAFT", "EXTERNAL_POST", "PAYOUT"):
            d = decide(context(action, mode="BOUNDED"))
            self.assertFalse(d.to_dict()["external_effects_authorized"])


if __name__ == "__main__":
    unittest.main()
