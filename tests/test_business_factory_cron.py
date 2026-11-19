"""The optional Business Factory cron tick must fail closed and leak no key."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "services/api/tools/cron/business_factory_tick.py"
VALUES = {
    "BUSINESS_FACTORY_RUN_URL": "https://valhalla-api-ha6a.onrender.com/api/business-factory/actions/run-once",
    "VALHALLA_FACTORY_KEY": "unit-test-only-key",
}


class FactoryCronTests(unittest.TestCase):
    def setUp(self):
        self.module = runpy.run_path(str(MODULE))
        self.tick = self.module["run_factory_tick"]

    def test_unconfigured_tick_skips_without_network(self):
        with patch.dict(os.environ, {"BUSINESS_FACTORY_RUN_URL": "", "VALHALLA_FACTORY_KEY": ""}):
            with patch("urllib.request.build_opener") as build:
                self.assertEqual(self.tick()["status"], "skipped")
                build.assert_not_called()

    def test_half_configured_tick_refuses(self):
        with patch.dict(os.environ, {
            "BUSINESS_FACTORY_RUN_URL": VALUES["BUSINESS_FACTORY_RUN_URL"],
            "VALHALLA_FACTORY_KEY": "",
        }):
            with self.assertRaisesRegex(RuntimeError, "configuration incomplete"):
                self.tick()

    def test_wrong_host_refuses_before_sending_key(self):
        bad = dict(VALUES, BUSINESS_FACTORY_RUN_URL="https://external.example/api/business-factory/actions/run-once")
        with patch.dict(os.environ, bad):
            with patch("urllib.request.build_opener") as build:
                with self.assertRaisesRegex(RuntimeError, "allowlist"):
                    self.tick()
                build.assert_not_called()

    def _network_response(self, response):
        body = io.BytesIO(json.dumps(response).encode("utf-8"))
        body.status = 200
        return body

    def test_idle_status_is_not_claimed_success(self):
        with patch.dict(os.environ, VALUES):
            with patch("urllib.request.build_opener") as build:
                build.return_value.open.return_value = self._network_response({
                    "status": "idle", "verified": False
                })
                result = self.tick()
                self.assertEqual(result, {"status": "idle", "verified": False})
                sent_request = build.return_value.open.call_args.args[0]
                self.assertEqual(sent_request.get_header("X-business-factory-key"), VALUES["VALHALLA_FACTORY_KEY"])

    def test_verified_internal_receipt_is_accepted_with_narrow_scope(self):
        receipt = {
            "status": "completed",
            "verified": True,
            "receipt": {
                "action_id": "bfd_123",
                "sha256": "abcdef",
                "verification_scope": "database_artifact_only",
                "external_effects": 0,
            },
        }
        with patch.dict(os.environ, VALUES):
            with patch("urllib.request.build_opener") as build:
                build.return_value.open.return_value = self._network_response(receipt)
                self.assertEqual(self.tick()["status"], "internal_artifact_verified")

    def test_forged_external_success_cannot_be_accepted(self):
        response = {"status": "completed", "verified": True, "receipt": {"external_effects": 1, "sha256": "abc"}}
        with patch.dict(os.environ, VALUES):
            with patch("urllib.request.build_opener") as build:
                build.return_value.open.return_value = self._network_response(response)
                with self.assertRaisesRegex(RuntimeError, "did not confirm"):
                    self.tick()


if __name__ == "__main__":
    unittest.main()
