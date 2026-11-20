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
                "action_id": "bfd_" + "a" * 32,
                "sha256": "b" * 64,
                "artifact_type": "product_listing_draft",
                "media_content_id": 1,
                "sales_verified": False,
                "verification_scope": "database_artifact_only",
                "external_effects": 0,
            },
        }
        with patch.dict(os.environ, VALUES):
            with patch("urllib.request.build_opener") as build:
                build.return_value.open.return_value = self._network_response(receipt)
                self.assertEqual(self.tick()["status"], "internal_artifact_verified")

    def test_blocked_result_is_not_success_and_preserves_emergency_stop(self):
        with patch.dict(os.environ, VALUES):
            with patch("urllib.request.build_opener") as build:
                for reason in ("MANDATE_EXPIRED", "EMERGENCY_STOP_ACTIVE"):
                    with self.subTest(reason=reason):
                        build.return_value.open.return_value = self._network_response({
                            "status": "blocked", "verified": False, "reason": reason
                        })
                        self.assertEqual(self.tick(), {
                            "status": "blocked", "verified": False,
                            "emergency_stop": reason == "EMERGENCY_STOP_ACTIVE",
                        })

    def test_malformed_and_contradictory_receipts_fail_closed(self):
        valid = {
            "action_id": "bfd_" + "a" * 32, "sha256": "b" * 64,
            "artifact_type": "product_listing_draft", "media_content_id": 1,
            "sales_verified": False, "external_effects": 0,
            "verification_scope": "database_artifact_only",
        }
        cases = [
            [], {"status": "completed", "verified": True, "receipt": []},
            {"status": "blocked", "verified": True},
        ]
        for key, value in (
            ("sales_verified", True), ("sales_verified", None),
            ("external_effects", False), ("external_effects", 0.0),
            ("sha256", "not-a-digest"), ("action_id", "wrong"),
            ("media_content_id", True), ("media_content_id", 0),
            ("artifact_type", "paid_order"),
        ):
            cases.append({"status": "completed", "verified": True,
                          "receipt": dict(valid, **{key: value})})
        with patch.dict(os.environ, VALUES):
            with patch("urllib.request.build_opener") as build:
                for index, response in enumerate(cases):
                    with self.subTest(index=index):
                        build.return_value.open.return_value = self._network_response(response)
                        with self.assertRaisesRegex(RuntimeError, "did not confirm"):
                            self.tick()

    def test_forged_external_success_cannot_be_accepted(self):
        response = {"status": "completed", "verified": True, "receipt": {"external_effects": 1, "sha256": "abc"}}
        with patch.dict(os.environ, VALUES):
            with patch("urllib.request.build_opener") as build:
                build.return_value.open.return_value = self._network_response(response)
                with self.assertRaisesRegex(RuntimeError, "did not confirm"):
                    self.tick()


class PollingWorkerTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(MODULE.with_name("business_factory_worker.py")))

    def test_requires_explicit_postgres_and_activation(self):
        enabled = {"VALHALLA_INTERNAL_FACTORY_WORKER_ENABLED": "1",
                   "DATABASE_URL": "postgresql://localhost/disposable"}
        check = self.mod["configuration_ready"]
        self.assertTrue(check(enabled))
        self.assertFalse(check({}))
        self.assertFalse(check(dict(enabled, DATABASE_URL="sqlite://")))
        self.assertFalse(check(dict(enabled, VALHALLA_INTERNAL_FACTORY_WORKER_ENABLED="0")))

    def test_error_backoff_and_emergency_stop_sleep(self):
        from unittest.mock import Mock
        stop = Mock()
        stop.is_set.side_effect = [False, False, False, True]
        work = Mock(side_effect=[RuntimeError("private secret"),
                                 {"status": "blocked", "verified": False, "emergency_stop": True},
                                 {"status": "idle", "verified": False}])
        lines = []
        self.assertEqual(self.mod["poll"](work, stop, interval=15, emit=lines.append), 0)
        self.assertEqual([call.args[0] for call in stop.wait.call_args_list], [30, 60, 15])
        self.assertIn("retry_pending", lines[0])
        self.assertNotIn("private secret", " ".join(lines))

    def test_once_returns_nonzero_for_block_or_failure(self):
        import threading
        self.assertEqual(self.mod["poll"](lambda: {"status": "blocked"}, threading.Event(),
                                          emit=lambda _: None, once=True), 2)
        self.assertEqual(self.mod["poll"](lambda: {"status": "idle"}, threading.Event(),
                                          emit=lambda _: None, once=True), 0)

    def test_tick_owns_session_and_rejects_external_claim(self):
        from unittest.mock import MagicMock, Mock
        factory = MagicMock()
        db = factory.return_value.__enter__.return_value
        check = Mock()
        execute = Mock(return_value={"status": "completed", "verified": True,
                      "receipt": {"external_effects": 1, "sales_verified": False,
                                  "verification_scope": "database_artifact_only"}})
        with self.assertRaises(RuntimeError):
            self.mod["tick"](factory, execute, check)
        check.assert_called_once_with(db)
        db.rollback.assert_called_once()
        factory.return_value.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()
