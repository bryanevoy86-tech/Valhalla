"""API process liveness must not imply the critical routers successfully loaded."""
from __future__ import annotations

from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[1]
MOD = runpy.run_path(str(ROOT / "services/api/app/core/route_integrity.py"))
REQUIRED = MOD["REQUIRED_ROUTER_NAMES"]
report = MOD["compute_router_integrity"]


class RouterIntegrityTests(unittest.TestCase):
    def test_all_required_routers_present(self):
        output = report(set(REQUIRED), {})
        self.assertTrue(output["ready"])
        self.assertEqual(output["missing"], [])
        self.assertEqual(output["loaded_count"], output["required_count"])

    def test_many_other_routers_does_not_mask_missing_auth(self):
        loaded = (set(REQUIRED) - {"auth_weweb"}) | {f"optional_{i}" for i in range(500)}
        output = report(loaded, {})
        self.assertFalse(output["ready"])
        self.assertEqual(output["missing"], ["auth_weweb"])

    def test_failed_mandatory_import_forces_red_readiness(self):
        out = report(set(REQUIRED) - {"marketing"}, {"marketing": "ImportError"})
        self.assertFalse(out["ready"])
        self.assertIn("marketing", out["missing"])
        self.assertEqual(out["import_failures"]["marketing"], "ImportError")

    def test_missing_factory_is_blocker(self):
        out = report(set(REQUIRED) - {"prime_business_factory"}, {})
        self.assertFalse(out["ready"])

    def test_release_and_independent_audit_routers_are_mandatory(self):
        for name in ("go_live", "system_status", "loki"):
            with self.subTest(name=name):
                self.assertIn(name, REQUIRED)
                self.assertFalse(report(set(REQUIRED) - {name})["ready"])

    def test_main_readyz_explicitly_checks_critical_router_state(self):
        source = (ROOT / "services/api/app/main.py").read_text(encoding="utf-8")
        self.assertIn('app.state.router_integrity = compute_router_integrity', source)
        self.assertIn('and router_ok', source)
        self.assertIn('status = 200 if ok else 503', source)


if __name__ == "__main__":
    unittest.main()
