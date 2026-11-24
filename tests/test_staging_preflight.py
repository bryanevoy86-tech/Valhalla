"""Exercise offline isolation checks with synthetic configuration only."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "staging_preflight", Path(__file__).resolve().parents[1] / "scripts/staging_preflight.py"
)
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)


class StagingPreflightTests(unittest.TestCase):
    def setUp(self):
        self.base = {"APP_ENV": "staging", "VALHALLA_STAGING_API_ORIGIN": "https://staging-api.example.invalid"}
        self.worker = {
            **self.base, "VALHALLA_STAGING_DATABASE_HOST": "dpg-stage-a",
            "DATABASE_URL": "postgresql://stage:synthetic@dpg-stage-a/valhalla_staging",
        }
        self.api = {
            **self.worker, "VALHALLA_PREVIEW_ORIGIN": "https://isolated-preview.example.invalid",
            "CORS_ALLOWED_ORIGINS": "https://isolated-preview.example.invalid", "VALHALLA_STRIPE_EVENT_MODE": "test",
            "VALHALLA_JWT_SECRET": "synthetic-jwt", "VALHALLA_LOKI_REVIEWER_KEY": "synthetic-reviewer",
            "VALHALLA_LOKI_REVIEWER_ID": "independent-fixture", "VALHALLA_OWNER_MANDATE_KEY": "synthetic-owner",
            "VALHALLA_PRIME_CONTROL_KEY": "synthetic-prime", "VALHALLA_FACTORY_KEY": "synthetic-factory",
        }
        self.reviewer = {
            **self.base, "VALHALLA_LOKI_QUEUE_URL": self.base["VALHALLA_STAGING_API_ORIGIN"],
            "VALHALLA_LOKI_REVIEWER_ID": "independent-fixture", "VALHALLA_LOKI_REVIEWER_KEY": "synthetic-reviewer",
        }

    def test_isolated_configuration_passes_offline(self):
        for role, env in (("api", self.api), ("worker", self.worker), ("reviewer", self.reviewer)):
            with self.subTest(role=role):
                self.assertEqual(stage.check(env, role), [])

    def test_refuses_production_hosts_and_ambiguous_private_targets(self):
        cases = [
            {"VALHALLA_STAGING_API_ORIGIN": "https://valhalla-api-ha6a.onrender.com"},
            {"CORS_ALLOWED_ORIGINS": "*"},
            {"VALHALLA_PREVIEW_ORIGIN": "https://isolated-preview.example.invalid/path"},
            {"DATABASE_URL": "postgresql://stage:synthetic@unapproved/valhalla_staging"},
            {"DATABASE_URL": self.worker["DATABASE_URL"] + "?host=elsewhere"},
            {"DATABASE_URL": self.worker["DATABASE_URL"].replace("dpg-stage-a", "dpg-d9ek3oj7uimc73fooes0-a"),
             "VALHALLA_STAGING_DATABASE_HOST": "dpg-d9ek3oj7uimc73fooes0-a"},
        ]
        for change in cases:
            with self.subTest(change=change):
                failures = stage.check({**self.api, **change}, "api")
                self.assertTrue(failures)
                self.assertNotIn("synthetic", " ".join(failures))

    def test_payment_and_reviewer_credentials_fail_closed(self):
        sandbox = {
            **self.api, "VALHALLA_STRIPE_READBACK_ENABLED": "1",
            "VALHALLA_STRIPE_TEST_WEBHOOK_SECRET": "whsec_fixture",
            "VALHALLA_STRIPE_READBACK_KEY": "rk_test_fixture", "VALHALLA_STRIPE_ACCOUNT_ID": "acct_fixture",
        }
        self.assertFalse(stage.check(sandbox, "api"))
        for change in ({"VALHALLA_STRIPE_READBACK_KEY": "rk_live_fixture"},
                       {"VALHALLA_STRIPE_DELIVERY_ENABLED": "1"},
                       {"VALHALLA_STRIPE_EVENT_MODE": "live"},
                       {"VALHALLA_PRIME_CONTROL_KEY": sandbox["VALHALLA_LOKI_REVIEWER_KEY"]}):
            self.assertTrue(stage.check({**sandbox, **change}, "api"))
        self.assertTrue(stage.check({**self.worker, "VALHALLA_LOKI_REVIEWER_KEY": "reviewer"}, "worker"))
        self.assertTrue(stage.check({**self.reviewer, "VALHALLA_LOKI_QUEUE_URL": "https://foreign.invalid"}, "reviewer"))
        self.assertTrue(stage.check({**self.reviewer, "DATABASE_URL": self.worker["DATABASE_URL"]}, "reviewer"))

    def test_refund_writer_isolated_settings(self):
        writer = {
            **self.worker, "VALHALLA_STRIPE_EVENT_MODE": "test", "VALHALLA_STRIPE_ACCOUNT_ID": "acct_fixture",
            "VALHALLA_STRIPE_SANDBOX_REFUND_ENABLED": "1", "VALHALLA_STRIPE_SANDBOX_REFUND_WRITE_KEY": "rk_test_fixture",
            "VALHALLA_STRIPE_SANDBOX_REFUND_API_VERSION": "2025-02-24.acacia",
            "VALHALLA_STRIPE_SANDBOX_REFUND_SCOPE": "a" * 64,
        }
        self.assertEqual(stage.check(writer, "refund-writer"), [])
        self.assertTrue(stage.check({**self.api, **writer}, "api"))
        for change in ({"VALHALLA_STRIPE_SANDBOX_REFUND_WRITE_KEY": "rk_live_fixture"},
                       {"VALHALLA_STRIPE_READBACK_KEY": "rk_test_other"},
                       {"VALHALLA_STRIPE_SANDBOX_REFUND_SCOPE": ""},
                       {"VALHALLA_LOKI_REVIEWER_KEY": "reviewer"},
                       {"VALHALLA_PRIME_CONTROL_KEY": "prime"}):
            self.assertTrue(stage.check({**writer, **change}, "refund-writer"))

    def test_signed_specialists_use_separate_logins_and_no_authority_keys(self):
        for role, login in stage.SPECIALISTS.items():
            env = {**self.worker, "DATABASE_URL": self.worker["DATABASE_URL"].replace("stage:", login + ":"),
                   stage.SPECIALIST_PRIVATE: "a" * 64, stage.ENROLLMENT_PUBLIC: "b" * 64}
            self.assertEqual(stage.check(env, role), [])
            other = "njord" if role == "odin" else "odin"
            self.assertTrue(stage.check(env, other))
            for name in (stage.ENROLLMENT_PRIVATE, "VALHALLA_OWNER_MANDATE_KEY", "VALHALLA_STRIPE_READBACK_KEY"):
                self.assertTrue(stage.check({**env, name: "dummy"}, role))
            self.assertTrue(stage.check({**self.api, stage.SPECIALIST_PRIVATE: "a" * 64}, "api"))

    def test_worker_launcher_stops_at_hold_before_starting_any_lane(self):
        import os
        import subprocess
        import sys
        import tempfile

        root = Path(stage.__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            fake_python = Path(temporary) / "python"
            fake_python.write_text(
                f'#!/bin/sh\ncase "$1" in scripts/staging_preflight.py) exec "{sys.executable}" "$@";; esac\n'
                'printf "unexpected worker lane\\n"; exit 1\n'
            )
            fake_python.chmod(0o700)
            env = {**self.worker, "PATH": temporary + os.pathsep + os.environ["PATH"]}
            result = subprocess.run(
                ["bash", "scripts/staging_workers.sh", "worker"], cwd=root, env=env,
                capture_output=True, text=True, timeout=5,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("worker hold is active", result.stderr)
        self.assertNotIn("unexpected worker lane", result.stdout)
