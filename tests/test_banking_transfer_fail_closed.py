"""No financial transfer may be reported executed without a real bank receipt.

This executes the existing capital/banking module without any bank credentials.
It is intentionally a NO-MONEY test.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import unittest

from capital.banking.approvals import create_approval
from capital.banking.executor import execute_internal_transfer
from capital.banking.kill_switch import KILL_SWITCH
from capital.banking.registry import INTERNAL_WHITELIST


class BankTransferGuardTests(unittest.TestCase):
    def setUp(self):
        self.old_whitelist = set(INTERNAL_WHITELIST)
        self.old_kill = KILL_SWITCH["enabled"]
        INTERNAL_WHITELIST.add("ci-destination")
        KILL_SWITCH["enabled"] = False
        self.approval = create_approval(
            "ci-transfer-123", "ci-source", "ci-destination", 100.0,
        )

    def tearDown(self):
        INTERNAL_WHITELIST.clear()
        INTERNAL_WHITELIST.update(self.old_whitelist)
        KILL_SWITCH["enabled"] = self.old_kill

    def test_approved_transfer_fails_closed_without_provider(self):
        with self.assertRaisesRegex(RuntimeError, "BANK_TRANSFER_PROVIDER_NOT_CONNECTED"):
            execute_internal_transfer(self.approval, "OPERATING")
        self.assertFalse(self.approval.used, "Do not consume an approval without bank settlement")

    def test_kill_switch_blocks_before_provider_check(self):
        KILL_SWITCH["enabled"] = True
        with self.assertRaisesRegex(RuntimeError, "KILL SWITCH ACTIVE"):
            execute_internal_transfer(self.approval, "OPERATING")
        self.assertFalse(self.approval.used)

    def test_unknown_destination_denied(self):
        self.approval.to_account = "outside-ci-whitelist"
        with self.assertRaisesRegex(RuntimeError, "Destination not whitelisted"):
            execute_internal_transfer(self.approval, "OPERATING")

    def test_expired_approval_denied(self):
        self.approval.expires_at = datetime.utcnow() - timedelta(seconds=1)
        with self.assertRaisesRegex(RuntimeError, "Approval expired"):
            execute_internal_transfer(self.approval, "OPERATING")

    def test_transfer_over_cap_denied(self):
        self.approval.amount = 999999.0
        with self.assertRaisesRegex(RuntimeError, "Transfer exceeds cap"):
            execute_internal_transfer(self.approval, "OPERATING")


if __name__ == "__main__":
    unittest.main()
