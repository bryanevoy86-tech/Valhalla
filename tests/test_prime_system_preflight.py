"""System-wide acceptance inventory must remain explicit and non-deceptive."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = runpy.run_path(str(ROOT / "scripts/prime_system_preflight.py"))
inspect_matrix = MODULE["inspect_matrix"]
SOURCE_MATRIX = ROOT / "ops/prime_system_integration_matrix.json"


class PrimeSystemPreflightTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(SOURCE_MATRIX.read_text(encoding="utf-8"))

    def test_current_manifest_has_all_source_anchors_and_no_false_production_claims(self):
        report = inspect_matrix(ROOT)
        self.assertTrue(report["ok"], report["issues"])
        self.assertGreaterEqual(report["capability_count"], 20)
        self.assertEqual(report["production_verified_count"], 0)
        self.assertIn("cannot prove", report["warning"])

    def _altered_report(self, alter):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "ops").mkdir()
            doc = copy.deepcopy(self.doc)
            alter(doc)
            (root / "ops/prime_system_integration_matrix.json").write_text(json.dumps(doc), encoding="utf-8")
            return inspect_matrix(root)

    def test_manifest_cannot_claim_live_without_receipt_and_commit(self):
        def alter(doc):
            row = doc["capabilities"][0]
            row["production_verified"] = True
            row["evidence_level"] = "SQLITE_INTEGRATION_TESTED"
        report = self._altered_report(alter)
        self.assertFalse(report["ok"])
        self.assertTrue(any("unsupported live claim" in x for x in report["issues"]))
        self.assertTrue(any("live_receipt" in x for x in report["issues"]))

    def test_unknown_dependencies_are_rejected(self):
        def alter(doc):
            doc["capabilities"][0]["depends_on"].append("imaginary_engine_not_built")
        report = self._altered_report(alter)
        self.assertTrue(any("unknown dependency" in x for x in report["issues"]))

    def test_missing_sources_are_not_treated_as_complete(self):
        report = self._altered_report(lambda doc: None)
        self.assertFalse(report["ok"])
        self.assertTrue(any("missing source" in x for x in report["issues"]))


if __name__ == "__main__":
    unittest.main()
