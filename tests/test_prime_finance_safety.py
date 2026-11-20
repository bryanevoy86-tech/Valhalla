"""Fail-closed finance contracts: signatures, webhook claims and payout receipts."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import runpy
import sys
import time
import types
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1] / "services/api/app"
SECRET = "whsec_test_not_a_real_key"


def _module(name: str, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


class FinanceSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = _module("app")
        app.__path__ = [str(ROOT)]
        providers = _module("app.providers")
        providers.__path__ = [str(ROOT / "providers")]
        base = _module("app.providers.base", ProviderAdapter=object)
        with patch.dict(sys.modules, {
            "app": app, "app.providers": providers, "app.providers.base": base,
        }):
            cls.adapter_module = runpy.run_path(str(ROOT / "providers/stripe_adapter.py"))

    def _signed_header(self, raw: bytes, timestamp: int, *, secret: str = SECRET):
        sig = hmac.new(secret.encode(), str(timestamp).encode() + b"." + raw, hashlib.sha256).hexdigest()
        return f"t={timestamp},v0=ignore,v1={sig},diagnostic=any"

    def test_valid_signature_and_multiple_headers(self):
        verifier = self.adapter_module["verify_stripe_signature"]
        now = 1795000000
        raw = b'{"id":"evt_123","type":"payment_intent.succeeded"}'
        self.assertTrue(verifier(raw, self._signed_header(raw, now), SECRET, now=now))
        self.assertTrue(verifier(raw, f"t={now},v1=bad,v1={self._signed_header(raw, now).split('v1=')[1].split(',')[0]}", SECRET, now=now))

    def test_missing_stale_future_modified_or_malformed_signature_rejected(self):
        verify = self.adapter_module["verify_stripe_signature"]
        now = 1795000000
        body = b'{"event":"original"}'
        header = self._signed_header(body, now)
        self.assertFalse(verify(body + b" ", header, SECRET, now=now))
        self.assertFalse(verify(body, header, None, now=now))
        self.assertFalse(verify(body, "t=bogus,v1=abc", SECRET, now=now))
        self.assertFalse(verify(body, self._signed_header(body, now - 301), SECRET, now=now))
        self.assertFalse(verify(body, self._signed_header(body, now + 301), SECRET, now=now))
        self.assertFalse(verify(body, header, "wrong_secret", now=now))

    def _make_webhook_client(self, live: bool):
        app_pkg = _module("app")
        app_pkg.__path__ = [str(ROOT)]
        heimdall = _module("app.heimdall")
        heimdall.__path__ = []
        authority = _module("app.heimdall.authority", is_live=lambda: live)
        providers = _module("app.providers")
        providers.__path__ = []
        adapter = _module("app.providers.stripe_adapter", StripeAdapter=self.adapter_module["StripeAdapter"])
        with patch.dict(sys.modules, {
            "app": app_pkg,
            "app.heimdall": heimdall,
            "app.heimdall.authority": authority,
            "app.providers": providers,
            "app.providers.stripe_adapter": adapter,
        }):
            router = runpy.run_path(str(ROOT / "webhooks/stripe.py"))["router"]
        api = FastAPI()
        api.include_router(router)
        return TestClient(api)

    def test_invalid_webhook_never_accepted_as_payment(self):
        with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": SECRET}):
            with self._make_webhook_client(True) as client:
                payload = {"id": "evt_fake", "type": "payment_intent.succeeded"}
                resp = client.post("/webhooks/stripe", json=payload)
                self.assertEqual(resp.status_code, 400)
                self.assertNotIn("payment_recorded", resp.text)

    def test_signed_webhook_still_requires_real_ledger_consumer(self):
        raw = json.dumps({"id": "evt_real", "type": "payment_intent.succeeded"}).encode()
        with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": SECRET}):
            with self._make_webhook_client(True) as client:
                resp = client.post("/webhooks/stripe", content=raw, headers={
                    "Stripe-Signature": self._signed_header(raw, int(time.time())),
                })
                self.assertEqual(resp.status_code, 503)
                self.assertIn("NOT_VERIFIED", resp.text)
                self.assertNotIn("payment_recorded", resp.text)

    def test_sandbox_webhook_has_no_money_effect(self):
        with self._make_webhook_client(False) as client:
            resp = client.post("/webhooks/stripe", json={"id": "evt_shadow", "type": "payment_intent.succeeded"})
            self.assertEqual(resp.status_code, 200)
            self.assertFalse(resp.json()["verified_financial_effect"])

    def test_live_payout_cannot_invent_a_stripe_payout_id(self):
        actions = _module("app.core.engines.actions", MONEY_MOVE="money_move")
        guard = _module("app.core.engines.guard_runtime", enforce_engine=lambda *args: None)
        runtime = _module("app.core.runtime_flags", is_live=lambda: True)
        app_pkg = _module("app")
        app_pkg.__path__ = [str(ROOT)]
        core = _module("app.core")
        core.__path__ = []
        engines = _module("app.core.engines")
        engines.__path__ = []
        with patch.dict(sys.modules, {
            "app": app_pkg, "app.core": core, "app.core.engines": engines,
            "app.core.engines.actions": actions,
            "app.core.engines.guard_runtime": guard,
            "app.core.runtime_flags": runtime,
        }):
            payout = runpy.run_path(str(ROOT / "integrations/stripe/payouts.py"))
        with self.assertRaisesRegex(RuntimeError, "NOT_IMPLEMENTED"):
            payout["payout_to_bank"](5000, "acct_test")
        self.assertEqual(payout["get_payout_status"]("po_guess")["status"], "unverified")


if __name__ == "__main__":
    unittest.main()
