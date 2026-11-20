"""Runtime route contract analyzer unit tests (no backend import side effects)."""
from __future__ import annotations

from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
ns = runpy.run_path(str(ROOT / "scripts/prime_runtime_route_probe.py"))
check = ns["inspect_route_contract"]
contracts = ns["MANDATORY_ENDPOINTS"]


class PrimeRouteProbeTests(unittest.TestCase):
    def test_all_required_routes_can_be_declared(self):
        routes = [SimpleNamespace(path=path, methods={method}) for method, path in contracts.values()]
        result = check(routes)
        self.assertTrue(result["ok"])
        self.assertEqual(result["missing"], [])
        self.assertEqual(result["registered"], result["required"])

    def test_missing_required_route_produces_failure(self):
        routes = [
            SimpleNamespace(path=path, methods={method})
            for name, (method, path) in contracts.items()
            if name != "factory_execution"
        ]
        result = check(routes)
        self.assertFalse(result["ok"])
        self.assertIn("factory_execution", result["missing"])

    def test_wrong_http_method_does_not_count_as_registered(self):
        routes = [
            SimpleNamespace(path=path, methods={"GET" if method == "POST" else "POST"})
            for method, path in contracts.values()
        ]
        result = check(routes)
        self.assertFalse(result["ok"])
        self.assertEqual(len(result["missing"]), len(contracts))

    def test_router_registration_is_not_considered_revenue_proof(self):
        routes = [SimpleNamespace(path=path, methods={method}) for method, path in contracts.values()]
        report = check(routes)
        self.assertIn("not a successful provider operation", report["warning"])


if __name__ == "__main__":
    unittest.main()
